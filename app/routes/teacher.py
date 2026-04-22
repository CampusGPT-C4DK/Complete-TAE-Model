from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from typing import List, Optional
import os
import logging
from datetime import datetime

from app.database import supabase, supabase_admin
from app.services.auth_service import AuthService
from app.services.storage_service import StorageService
from app.services.pdf_processor import extract_text
from app.services.assignment_generator import generate_questions
from app.services.assignment_pdf import generate_assignment_pdf
from app.core.security import verify_jwt_token, is_faculty_role

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
        
        # Verify faculty role
        if result.get("role") != "faculty":
            logger.warning(f"Non-faculty user attempted faculty login: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only faculty can login to this endpoint"
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
    files: List[UploadFile] = File(...),
    difficulty: str = Form(...),
    assignment_no: str = Form(...),
    subject: str = Form(...),
    branch: str = Form(...),
    semester: str = Form(...),
    faculty: str = Form(...),
    given_date: str = Form(...),
    submission_date: str = Form(...),
    faculty_user: dict = Depends(get_current_faculty)
):
    """
    Upload teacher notes, generate assignment, and store in Supabase Storage.
    Faculty must be authenticated.
    """
    try:
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
        
        for i, file in enumerate(files):
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
        for file in files:
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
        
        # Fetch evaluations with submission details
        data = supabase.table("evaluations") \
            .select("""
                id,
                total_marks,
                marks_obtained,
                percentage,
                grade,
                feedback,
                evaluated_at,
                submissions(student_id, submitted_at, is_late, days_late, status)
            """) \
            .eq("assignment_id", assignment_id) \
            .execute()
        
        formatted = []
        for row in data.data:
            submission = row.get("submissions", {})
            student_id = submission.get("student_id") if submission else None
            
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
            
            formatted.append({
                "student_id": student_id,
                "student_name": student_info.get("full_name", "N/A"),
                "email": student_info.get("email", "N/A"),
                "marks": row.get("marks_obtained"),
                "total_marks": row.get("total_marks"),
                "percentage": row.get("percentage"),
                "grade": row.get("grade"),
                "feedback": row.get("feedback"),
                "late_days": submission.get("days_late") if submission else 0,
                "status": submission.get("status") if submission else "pending",
                "submitted_at": submission.get("submitted_at") if submission else None,
                "evaluated_at": row.get("evaluated_at")
            })
        
        logger.info(f"✓ Found {len(formatted)} submissions")
        
        return {"status": "success", "count": len(formatted), "data": formatted}
        
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching submissions: {str(e)}")
        return {"status": "error", "message": str(e)}