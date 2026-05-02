from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, status, Depends, Request, Body
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.security import HTTPBearer
from typing import List, Optional, Union
import os
import logging
from datetime import datetime
from io import BytesIO

from app.database import supabase, supabase_admin
from app.services.auth_service import AuthService
from app.services.storage_service import StorageService, ASSIGNMENTS_BUCKET, TEACHER_NOTES_BUCKET, SUBMISSIONS_BUCKET
from app.services.pdf_processor import extract_text
from app.services.assignment_generator import generate_questions
from app.services.assignment_pdf import generate_assignment_pdf
from app.core.security import verify_jwt_token, is_faculty_role, is_admin_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/teacher", tags=["Teacher"])

# Initialize storage buckets
StorageService.ensure_buckets_exist()

# HTTPBearer security scheme for Swagger integration
security = HTTPBearer()


# --------------------------------------------------
# 📅 DATE FORMAT HANDLER
# --------------------------------------------------
def format_date(date_str: str):
    """Parse date string in multiple formats."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        try:
            return datetime.strptime(date_str, "%d-%m-%Y").date()
        except:
            try:
                return datetime.strptime(date_str, "%d/%m/%Y").date()
            except:
                return datetime.strptime(date_str, "%y-%m-%d").date()


# --------------------------------------------------
# 🔐 HELPER: Verify Token and Get Faculty User
# --------------------------------------------------
def verify_faculty_token(token: str):
    """Verify a token string and return faculty user info."""
    try:
        if not token:
            raise ValueError("No token provided")
        
        # Remove "Bearer " prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        logger.info(f"Token received: {token[:50]}...")
        
        # Verify token with Supabase
        user_info = AuthService.verify_token_and_get_user(token)
        logger.info(f"Token verified for user: {user_info.get('user_id')}")
        
        # Check if faculty role
        if not is_faculty_role(user_info.get("role")):
            logger.warning(f"Non-faculty user attempted faculty endpoint: {user_info.get('role')}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only faculty can access this endpoint"
            )
        
        return user_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


# --------------------------------------------------
# 🔐 DEPENDENCY: GET CURRENT FACULTY USER
# --------------------------------------------------
def get_current_faculty(credentials = Depends(security)):
    """Extract and verify faculty user from JWT token."""
    try:
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )
        
        token = credentials.credentials
        return verify_faculty_token(token)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


# --------------------------------------------------
# 📝 FACULTY REGISTER (Using Backend Auth)
# --------------------------------------------------
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_faculty(
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    subject: str = Form(default="General")
):
    """
    Register a new faculty member.
    Uses Supabase Auth + user_profiles table from backend.
    """
    try:
        logger.info(f"📝 Faculty registration: {email}")
        
        # Register using backend auth system
        result = AuthService.register_user(
            email=email,
            password=password,
            full_name=full_name,
            role="faculty"
        )
        
        # Store additional faculty info (using service role to bypass RLS)
        faculty_db = supabase_admin if supabase_admin else supabase
        try:
            faculty_db.table("faculty_metadata").insert({
                "user_id": result["user_id"],
                "subject": subject,
                "is_verified": False
            }).execute()
            logger.info(f"✓ Faculty metadata created: {result['user_id']}")
        except Exception as metadata_err:
            logger.warning(f"⚠️ Could not create faculty metadata (non-blocking): {str(metadata_err)}")
        
        logger.info(f"✅ Faculty registered: {email}")
        
        return {
            "status": "success",
            "user_id": result["user_id"],
            "email": result["email"],
            "full_name": result["full_name"],
            "role": result["role"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"]
        }
        
    except Exception as e:
        logger.error(f"❌ Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# --------------------------------------------------
# 🔐 FACULTY LOGIN (Using Backend Auth)
# --------------------------------------------------
@router.post("/login")
def login_faculty(
    email: str = Form(...),
    password: str = Form(...)
):
    """
    Login faculty member.
    Uses Supabase Auth + user_profiles table from backend.
    """
    try:
        logger.info(f"🔐 Faculty login: {email}")
        
        # Login using backend auth system
        result = AuthService.login_user(
            email=email,
            password=password
        )
        
        # Allow both faculty and admin roles for teacher/faculty access.
        if not is_faculty_role(result.get("role")):
            logger.warning(f"Non-faculty/admin user attempted faculty login: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only faculty or admin can login to this endpoint"
            )
        
        logger.info(f"✅ Faculty login successful: {email}")
        
        return {
            "status": "success",
            "user_id": result["user_id"],
            "email": result["email"],
            "full_name": result["full_name"],
            "role": result["role"],
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


# --------------------------------------------------
# 📤 UPLOAD NOTES & GENERATE ASSIGNMENT
# --------------------------------------------------
@router.post("/upload-notes")
async def upload_notes(
    request: Request,
    files: Optional[Union[UploadFile, List[UploadFile]]] = File(None),
    difficulty: Optional[str] = Form(None),
    assignment_no: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    branch: Optional[str] = Form(None),
    semester: Optional[str] = Form(None),
    faculty: Optional[str] = Form(None),
    given_date: Optional[str] = Form(None),
    submission_date: Optional[str] = Form(None),
    faculty_user: dict = Depends(get_current_faculty)
):
    """
    Upload teacher notes, generate assignment, and store in Supabase Storage.
    Faculty must be authenticated.
    """
    try:
        # Be permissive with multipart keys to support older/newer frontend payloads.
        # This avoids 422 validation failures for minor field-name differences.
        form_data = await request.form()

        uploaded_files: List[UploadFile] = []
        if isinstance(files, list):
            uploaded_files.extend(files)
        elif files is not None:
            uploaded_files.append(files)

        if not uploaded_files:
            uploaded_files.extend(form_data.getlist("files") or form_data.getlist("file"))
        uploaded_files = [f for f in uploaded_files if hasattr(f, "filename")]

        difficulty = difficulty or form_data.get("difficulty")
        assignment_no = assignment_no or form_data.get("assignment_no") or form_data.get("assignmentNo")
        subject = subject or form_data.get("subject")
        branch = branch or form_data.get("branch")
        semester = semester or form_data.get("semester")
        faculty = faculty or form_data.get("faculty") or faculty_user.get("full_name") or "Faculty"
        given_date = given_date or form_data.get("given_date") or form_data.get("givenDate")
        submission_date = submission_date or form_data.get("submission_date") or form_data.get("submissionDate")

        if not uploaded_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files received. Please select at least one PDF file."
            )
        if not all([difficulty, assignment_no, subject, branch, semester, given_date, submission_date]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields. Required: difficulty, assignment_no, subject, branch, semester, given_date, submission_date."
            )

        # Get user_id from verified faculty user
        user_id = faculty_user["user_id"]
        
        logger.info(f"📤 Faculty {user_id} uploading notes for assignment {assignment_no}")
        
        # Parse dates
        given_date_obj = format_date(given_date)
        submission_date_obj = format_date(submission_date)
        
        # Create temp directory
        os.makedirs("teacher_uploads", exist_ok=True)
        
        # Extract text from all uploaded files
        unit_notes = {}
        storage_urls = {}
        
        for i, file in enumerate(uploaded_files):
            file_path = f"teacher_uploads/{file.filename}"
            
            logger.info(f"   Processing file {i+1}: {file.filename}")
            
            # Save locally
            with open(file_path, "wb") as buffer:
                buffer.write(file.file.read())
            
            # Extract text
            text = extract_text(file_path)
            if not text:
                logger.error(f"   Text extraction failed for {file.filename}")
                return {
                    "status": "error",
                    "message": f"Extraction failed for {file.filename}"
                }
            
            unit_notes[f"Unit {i+1}"] = text
            
            # Upload to Supabase Storage
            try:
                storage_result = StorageService.upload_teacher_notes(
                    file_path=file_path,
                    user_id=user_id,
                    subject=subject,
                    assignment_no=assignment_no
                )
                storage_urls[f"Unit {i+1}"] = storage_result["storage_url"]
                logger.info(f"   ✓ File stored in Supabase: {storage_result['file_path']}")
            except Exception as e:
                logger.warning(f"   Storage upload failed (continuing): {str(e)}")
        
        # Generate questions using the extracted notes
        logger.info("   Generating assignment questions...")
        questions = generate_questions(unit_notes, difficulty)
        
        # Generate PDF
        logger.info("   Generating assignment PDF...")
        pdf_path = generate_assignment_pdf(
            questions,
            assignment_no,
            subject,
            branch,
            semester,
            "Multiple Units",
            faculty,
            str(given_date_obj),
            str(submission_date_obj)
        )
        
        # Upload PDF to Supabase Storage
        logger.info("   Uploading PDF to Supabase Storage...")
        pdf_storage_result = StorageService.upload_assignment_pdf(
            file_path=pdf_path,
            user_id=user_id,
            subject=subject,
            assignment_no=assignment_no,
            semester=semester
        )
        
        logger.info(f"   ✓ PDF stored: {pdf_storage_result['file_path']}")
        
        # Save assignment metadata to database
        logger.info("   Saving assignment metadata to database...")
        
        # ✅ CRITICAL: Use service role client to bypass RLS policies
        if not supabase_admin:
            logger.error("❌ SERVICE_ROLE_KEY not configured in .env!")
            logger.error("   This is required to bypass Row-Level Security (RLS) policies")
            logger.error("   Create assignment will fail with 403 Forbidden error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error: SERVICE_ROLE_KEY is missing from .env. Contact admin."
            )
        
        try:
            logger.info(f"   Using SERVICE_ROLE_KEY to bypass RLS (faculty_id: {user_id})")
            
            assignment = supabase_admin.table("assignments").insert({
                "faculty_id": user_id,  # ← RLS policy checks: faculty_id = auth.uid()
                "assignment_no": assignment_no,
                "subject": subject,
                "branch": branch,
                "semester": semester,
                "difficulty": difficulty,
                "given_date": str(given_date_obj),
                "submission_date": str(submission_date_obj),
                "questions": str(questions)[:5000],
                "pdf_storage_path": pdf_storage_result["file_path"],
                "pdf_url": pdf_storage_result["storage_url"],
                "teacher_notes_urls": storage_urls,
                "created_by": faculty_user.get("full_name", faculty),
                "status": "active"
            }).execute()
            
            if not assignment.data:
                logger.error("Database insert returned empty data")
                return {"status": "error", "message": "Failed to save assignment"}
            
            logger.info(f"✅ Assignment created: {assignment.data[0]['id']}")
            
        except Exception as db_error:
            logger.error(f"❌ Database insert error: {str(db_error)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Failed to save assignment: {str(db_error)}"
            )
        
        # Clean up local files
        for file in uploaded_files:
            file_path = f"teacher_uploads/{file.filename}"
            if os.path.exists(file_path):
                os.remove(file_path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        
        return {
            "status": "success",
            "message": "Assignment created and stored successfully",
            "assignment_id": assignment.data[0]["id"],
            "pdf_url": pdf_storage_result["storage_url"],
            "storage_bucket": pdf_storage_result["bucket"],
            "storage_path": pdf_storage_result["file_path"]
        }
        
    except HTTPException as he:
        logger.error(f"❌ HTTP Error: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📚 VIEW MY ASSIGNMENTS
# --------------------------------------------------
@router.get("/my-assignments")
def get_my_assignments(faculty_user: dict = Depends(get_current_faculty)):
    """Get all assignments created by the logged-in faculty."""
    try:
        # Get user_id from verified faculty user
        user_id = faculty_user["user_id"]
        
        logger.info(f"Fetching assignments for faculty: {user_id}")
        
        data = supabase.table("assignments") \
            .select("*") \
            .eq("faculty_id", user_id) \
            .order("created_at", desc=True) \
            .execute()
        
        logger.info(f"✓ Found {len(data.data)} assignments")
        
        # Add download URLs for each assignment
        for assignment in data.data:
            assignment["download_url"] = f"/teacher/download-assignment/{assignment['id']}"
            
            # Process teacher notes URLs
            teacher_notes_urls = assignment.get("teacher_notes_urls") or {}
            if isinstance(teacher_notes_urls, dict):
                for subject_key in teacher_notes_urls.keys():
                    teacher_notes_urls[subject_key] = f"/teacher/download-teacher-notes/{assignment['id']}/{subject_key}"
                assignment["teacher_notes_urls"] = teacher_notes_urls
        
        return {"status": "success", "count": len(data.data), "data": data.data}
        
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching assignments: {str(e)}")
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📊 TRACK SUBMISSIONS (PER ASSIGNMENT)
# --------------------------------------------------
@router.get("/track-submissions/{assignment_id}")
def track_submissions(
    assignment_id: str,
    faculty_user: dict = Depends(get_current_faculty)
):
    """Track submissions for a specific assignment."""
    try:
        
        logger.info(f"Fetching submissions for assignment: {assignment_id}")
        
        # Fetch submission records first so status is always visible, even before/without evaluation.
        submission_rows = supabase.table("submissions") \
            .select("""
                id,
                student_id,
                submitted_at,
                is_late,
                days_late,
                status
            """) \
            .eq("assignment_id", assignment_id) \
            .order("submitted_at", desc=True) \
            .execute()
        
        formatted = []
        for submission in submission_rows.data:
            student_id = submission.get("student_id")
            
            # Get student profile (if we need full_name and email)
            student_info = {}
            if student_id:
                try:
                    student_data = supabase.table("user_profiles") \
                        .select("full_name, email") \
                        .eq("id", student_id) \
                        .single() \
                        .execute()
                    if student_data.data:
                        student_info = student_data.data
                except Exception as e:
                    logger.warning(f"Could not fetch student profile for {student_id}: {str(e)}")

            # Get evaluation data if graded/evaluated
            evaluation_data = {}
            try:
                eval_result = supabase.table("evaluations") \
                    .select("total_marks, marks_obtained, percentage, grade, feedback, evaluated_at") \
                    .eq("submission_id", submission.get("id")) \
                    .limit(1) \
                    .execute()
                if eval_result.data:
                    evaluation_data = eval_result.data[0]
            except Exception as e:
                logger.warning(f"Could not fetch evaluation for submission {submission.get('id')}: {str(e)}")
            
            formatted.append({
                "student_id": student_id,
                "student_name": student_info.get("full_name", "N/A"),
                "email": student_info.get("email", "N/A"),
                "marks": evaluation_data.get("marks_obtained"),
                "total_marks": evaluation_data.get("total_marks"),
                "percentage": evaluation_data.get("percentage"),
                "grade": evaluation_data.get("grade"),
                "feedback": evaluation_data.get("feedback"),
                "late_days": submission.get("days_late", 0),
                "status": submission.get("status", "pending"),
                "submitted_at": submission.get("submitted_at"),
                "evaluated_at": evaluation_data.get("evaluated_at")
            })
        
        logger.info(f"✓ Found {len(formatted)} submissions")
        
        return {"status": "success", "count": len(formatted), "data": formatted}
        
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching submissions: {str(e)}")
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 🗑️ DELETE ASSIGNMENT (DB + STORAGE)
# --------------------------------------------------
@router.delete("/assignments/{assignment_id}")
def delete_assignment(
    assignment_id: str,
    faculty_user: dict = Depends(get_current_faculty)
):
    """
    Delete an assignment created by the faculty (or admin).
    - Removes assignment row (cascades to submissions/evaluations via FK constraints)
    - Best-effort deletes related storage objects (pdf + notes + submission files)
    """
    try:
        db_client = supabase_admin if supabase_admin else supabase
        requester_id = faculty_user.get("user_id")
        requester_role = faculty_user.get("role", "")

        # Fetch assignment to validate ownership and get storage paths
        assignment_res = db_client.table("assignments") \
            .select("id, faculty_id, pdf_storage_path, teacher_notes_urls") \
            .eq("id", assignment_id) \
            .limit(1) \
            .execute()

        if not assignment_res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        assignment = assignment_res.data[0]
        owner_id = assignment.get("faculty_id")

        # Only owner faculty or admin can delete
        if owner_id != requester_id and not is_admin_role(requester_role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to delete this assignment")

        # Best-effort: delete submission files (if any) from storage
        try:
            subs_res = db_client.table("submissions") \
                .select("submitted_file_path") \
                .eq("assignment_id", assignment_id) \
                .execute()
            for row in (subs_res.data or []):
                p = row.get("submitted_file_path")
                if p:
                    try:
                        StorageService.delete_file(SUBMISSIONS_BUCKET, p)
                    except Exception as e:
                        logger.warning(f"Could not delete submission file {p}: {str(e)}")
        except Exception as e:
            logger.warning(f"Could not list submission files for deletion: {str(e)}")

        # Best-effort: delete assignment PDF
        pdf_path = assignment.get("pdf_storage_path")
        if pdf_path:
            try:
                StorageService.delete_file(ASSIGNMENTS_BUCKET, pdf_path)
            except Exception as e:
                logger.warning(f"Could not delete assignment PDF {pdf_path}: {str(e)}")

        # Best-effort: delete teacher notes (URLs stored as public URLs; derive paths)
        teacher_notes_urls = assignment.get("teacher_notes_urls") or {}
        if isinstance(teacher_notes_urls, dict):
            for _, url in teacher_notes_urls.items():
                try:
                    if not isinstance(url, str) or f"/{TEACHER_NOTES_BUCKET}/" not in url:
                        continue
                    storage_path = url.split(f"/{TEACHER_NOTES_BUCKET}/", 1)[1].split("?", 1)[0]
                    StorageService.delete_file(TEACHER_NOTES_BUCKET, storage_path)
                except Exception as e:
                    logger.warning(f"Could not delete teacher note from url {url}: {str(e)}")

        # Delete the assignment row (cascades)
        db_client.table("assignments").delete().eq("id", assignment_id).execute()

        return {"status": "success", "message": "Assignment deleted", "assignment_id": assignment_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting assignment: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# --------------------------------------------------
# ✏️ GET/UPDATE ASSIGNMENT (EDIT FLOW)
# --------------------------------------------------
@router.get("/assignments/{assignment_id}")
def get_assignment_by_id(
    assignment_id: str,
    faculty_user: dict = Depends(get_current_faculty)
):
    """Fetch a single assignment for editing (owner faculty or admin)."""
    try:
        db_client = supabase_admin if supabase_admin else supabase
        requester_id = faculty_user.get("user_id")
        requester_role = faculty_user.get("role", "")

        res = db_client.table("assignments").select("*").eq("id", assignment_id).limit(1).execute()
        if not res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        assignment = res.data[0]
        owner_id = assignment.get("faculty_id")
        if owner_id != requester_id and not is_admin_role(requester_role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to view this assignment")

        # Add download URL for private bucket access
        assignment["download_url"] = f"/teacher/download-assignment/{assignment_id}"
        
        # Process teacher notes URLs
        teacher_notes_urls = assignment.get("teacher_notes_urls") or {}
        if isinstance(teacher_notes_urls, dict):
            for subject_key in teacher_notes_urls.keys():
                # Replace with backend download endpoints instead of direct Supabase URLs
                teacher_notes_urls[subject_key] = f"/teacher/download-teacher-notes/{assignment_id}/{subject_key}"
            assignment["teacher_notes_urls"] = teacher_notes_urls

        return {"status": "success", "data": assignment}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching assignment: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/assignments/{assignment_id}")
def update_assignment(
    assignment_id: str,
    payload: dict = Body(default={}),
    faculty_user: dict = Depends(get_current_faculty)
):
    """
    Update assignment fields.
    Supports deactivation by setting status to 'archived' (UI shows Closed).
    """
    try:
        db_client = supabase_admin if supabase_admin else supabase
        requester_id = faculty_user.get("user_id")
        requester_role = faculty_user.get("role", "")

        res = db_client.table("assignments").select("faculty_id").eq("id", assignment_id).limit(1).execute()
        if not res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        owner_id = res.data[0].get("faculty_id")
        if owner_id != requester_id and not is_admin_role(requester_role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to edit this assignment")

        allowed = {
            "assignment_no",
            "subject",
            "branch",
            "semester",
            "difficulty",
            "given_date",
            "submission_date",
            "status",
            "created_by",
        }
        update_data = {k: v for k, v in (payload or {}).items() if k in allowed}
        if not update_data:
            return {"status": "success", "message": "Nothing to update"}

        db_client.table("assignments").update(update_data).eq("id", assignment_id).execute()
        return {"status": "success", "message": "Assignment updated", "assignment_id": assignment_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating assignment: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# 📥 DOWNLOAD ENDPOINTS (for private buckets)
# ============================================================================

@router.get("/download-assignment/{assignment_id}")
def download_assignment_pdf(
    assignment_id: str,
    faculty_user: dict = Depends(get_current_faculty)
):
    """
    Download assignment PDF from private bucket.
    Works for both faculty (owner) and admin.
    """
    try:
        db_client = supabase_admin if supabase_admin else supabase
        requester_id = faculty_user.get("user_id")
        requester_role = faculty_user.get("role", "")

        # Fetch assignment
        res = db_client.table("assignments").select("*").eq("id", assignment_id).limit(1).execute()
        if not res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        assignment = res.data[0]
        owner_id = assignment.get("faculty_id")
        
        # Check permission (owner or admin)
        if owner_id != requester_id and not is_admin_role(requester_role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to download this assignment")

        pdf_path = assignment.get("pdf_storage_path")
        if not pdf_path:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment PDF not found")

        # Download from private bucket
        logger.info(f"📥 Downloading assignment: {pdf_path}")
        file_content = StorageService.download_file(ASSIGNMENTS_BUCKET, pdf_path)

        # Extract filename from path
        filename = os.path.basename(pdf_path)

        # Return as streaming response
        return StreamingResponse(
            iter([file_content]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Download assignment failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/download-teacher-notes/{assignment_id}/{subject_key}")
def download_teacher_notes(
    assignment_id: str,
    subject_key: str,
    faculty_user: dict = Depends(get_current_faculty)
):
    """
    Download teacher notes from private bucket.
    subject_key is used to identify which note file to download (e.g., 'No SQL')
    """
    try:
        db_client = supabase_admin if supabase_admin else supabase
        requester_id = faculty_user.get("user_id")
        requester_role = faculty_user.get("role", "")

        # Fetch assignment
        res = db_client.table("assignments").select("*").eq("id", assignment_id).limit(1).execute()
        if not res.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        assignment = res.data[0]
        owner_id = assignment.get("faculty_id")
        
        # Check permission
        if owner_id != requester_id and not is_admin_role(requester_role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to download these notes")

        teacher_notes_urls = assignment.get("teacher_notes_urls") or {}
        
        # Get URL for this subject
        if not isinstance(teacher_notes_urls, dict) or subject_key not in teacher_notes_urls:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Teacher notes for '{subject_key}' not found")

        file_url = teacher_notes_urls[subject_key]
        
        # Extract storage path from URL
        if f"/{TEACHER_NOTES_BUCKET}/" not in file_url:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file URL")

        storage_path = file_url.split(f"/{TEACHER_NOTES_BUCKET}/", 1)[1].split("?", 1)[0]

        # Download from private bucket
        logger.info(f"📥 Downloading teacher notes: {storage_path}")
        file_content = StorageService.download_file(TEACHER_NOTES_BUCKET, storage_path)

        # Extract filename
        filename = os.path.basename(storage_path)

        # Return as streaming response
        return StreamingResponse(
            iter([file_content]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Download teacher notes failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))