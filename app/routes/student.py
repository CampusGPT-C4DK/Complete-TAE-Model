from fastapi import APIRouter, UploadFile, File, Form, Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from typing import List, Optional
import os
import logging
from datetime import datetime, timedelta

from app.database import supabase, supabase_admin
from app.services.auth_service import AuthService
from app.services.storage_service import StorageService
from app.services.pdf_processor import extract_text
from app.core.security import verify_jwt_token, is_student_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/student", tags=["Student"])

# Initialize storage buckets
StorageService.ensure_buckets_exist()

# HTTPBearer security scheme for Swagger integration
security = HTTPBearer()


# --------------------------------------------------
# 🔐 DEPENDENCY: GET CURRENT STUDENT USER
# --------------------------------------------------
def get_current_student(credentials = Depends(security)):
    """Extract and verify student user from JWT token."""
    try:
        token = credentials.credentials
        logger.info(f"Token received: {token[:50]}...")
        
        # Verify token with Supabase
        user_info = AuthService.verify_token_and_get_user(token)
        logger.info(f"Token verified for user: {user_info.get('user_id')}")
        
        # Check if student role
        if not is_student_role(user_info.get("role")):
            logger.warning(f"Non-student user attempted student endpoint: {user_info.get('role')}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can access this endpoint"
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
# 📝 STUDENT REGISTER (Using Backend Auth)
# --------------------------------------------------
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_student(
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...)
):
    """
    Register a new student.
    Uses Supabase Auth + user_profiles table from backend.
    """
    try:
        logger.info(f"📝 Student registration: {email}")
        
        # Register using backend auth system
        result = AuthService.register_user(
            email=email,
            password=password,
            full_name=full_name,
            role="student"
        )
        
        logger.info(f"✅ Student registered: {email}")
        
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
# 🔐 STUDENT LOGIN (Using Backend Auth)
# --------------------------------------------------
@router.post("/login")
def login_student(
    email: str = Form(...),
    password: str = Form(...)
):
    """
    Login student.
    Uses Supabase Auth + user_profiles table from backend.
    """
    try:
        logger.info(f"🔐 Student login: {email}")
        
        # Login using backend auth system
        result = AuthService.login_user(
            email=email,
            password=password
        )
        
        # Verify student role
        if result.get("role") != "student":
            logger.warning(f"Non-student user attempted student login: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only students can login to this endpoint"
            )
        
        logger.info(f"✅ Student login successful: {email}")
        
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
# 📤 SUBMIT ASSIGNMENT (With Supabase Storage)
# --------------------------------------------------
@router.post("/submit-assignment")
async def submit_assignment(
    assignment_id: str = Form(...),
    file: UploadFile = File(...),
    student_user: dict = Depends(get_current_student)
):
    """
    Submit an assignment solution.
    Student must be authenticated.
    Files stored in Supabase Storage.
    """
    try:
        # Get student_id from verified user
        student_id = student_user["user_id"]
        
        logger.info(f"📤 Student {student_id} submitting assignment {assignment_id}")
        
        # Validate file
        if not file.filename.endswith(".pdf"):
            logger.warning(f"Invalid file type: {file.filename}")
            return {"status": "error", "message": "Only PDF files allowed"}

        # Create temp directory
        os.makedirs("student_uploads", exist_ok=True)
        local_file_path = f"student_uploads/{file.filename}"

        # Save locally temporarily
        with open(local_file_path, "wb") as buffer:
            buffer.write(file.file.read())

        logger.info(f"   ✓ File saved temporarily: {local_file_path}")

        # Extract text from submission (optional - don't fail if extraction fails)
        logger.info("   Extracting text from submission...")
        submission_text = ""
        try:
            submission_text = extract_text(local_file_path)
            if not submission_text:
                logger.warning("   ⚠️ PDF text extraction returned empty - proceeding without text")
                submission_text = "[PDF content could not be extracted]"
        except Exception as e:
            logger.warning(f"   ⚠️ PDF text extraction failed: {str(e)} - proceeding without text")
            submission_text = "[PDF content could not be extracted]"

        # Get assignment data
        logger.info("   Fetching assignment details...")
        assignment = supabase.table("assignments") \
            .select("*") \
            .eq("id", assignment_id) \
            .execute()

        if not assignment.data:
            logger.error(f"   Assignment not found: {assignment_id}")
            return {"status": "error", "message": "Assignment not found"}

        assignment_data = assignment.data[0]
        submission_date_str = assignment_data["submission_date"]
        
        # Parse submission date
        try:
            submission_deadline = datetime.strptime(submission_date_str, "%Y-%m-%d").date() if isinstance(submission_date_str, str) else submission_deadline
        except:
            submission_deadline = datetime.now().date()

        # Check if late
        today = datetime.now().date()
        is_late = today > submission_deadline
        days_late = max(0, (today - submission_deadline).days) if is_late else 0

        logger.info(f"   Days late: {days_late}")

        # Upload to Supabase Storage
        logger.info("   Uploading to Supabase Storage...")
        try:
            storage_result = StorageService.upload_file_to_submissions(
                file_path=local_file_path,
                assignment_id=assignment_id,
                student_id=student_id,
                file_name=file.filename
            )
            logger.info(f"   ✓ File stored: {storage_result['file_path']}")
        except Exception as storage_error:
            logger.error(f"   ❌ Storage upload failed: {str(storage_error)}", exc_info=True)
            return {"status": "error", "message": f"File upload failed: {str(storage_error)}"}

        # Check if submission already exists (use admin client to bypass RLS for read)
        db_client = supabase_admin if supabase_admin else supabase
        existing_submission = db_client.table("submissions") \
            .select("id") \
            .eq("assignment_id", assignment_id) \
            .eq("student_id", student_id) \
            .execute()

        submission_id = None
        
        if existing_submission.data:
            # Update existing submission
            logger.info("   Updating existing submission...")
            submission_id = existing_submission.data[0]["id"]
            
            try:
                # Use admin client for update (student is already authenticated)
                db_client = supabase_admin if supabase_admin else supabase
                result = db_client.table("submissions").update({
                    "submitted_file_path": storage_result["file_path"],
                    "submitted_file_url": storage_result["storage_url"],
                    "submission_text": submission_text[:5000],
                    "submitted_at": datetime.now().isoformat(),
                    "is_late": is_late,
                    "days_late": days_late,
                    "status": "late" if is_late else "submitted",
                    "updated_at": datetime.now().isoformat()
                }).eq("id", submission_id).execute()
                
                logger.info(f"   ✓ Submission updated: {submission_id}")
            except Exception as db_error:
                logger.error(f"   ❌ Database update failed: {str(db_error)}", exc_info=True)
                return {"status": "error", "message": f"Failed to update submission: {str(db_error)}"}
        else:
            # Create new submission
            logger.info("   Creating new submission...")
            try:
                # Use admin client for insert (student is already authenticated)
                db_client = supabase_admin if supabase_admin else supabase
                result = db_client.table("submissions").insert({
                    "assignment_id": assignment_id,
                    "student_id": student_id,
                    "submitted_file_path": storage_result["file_path"],
                    "submitted_file_url": storage_result["storage_url"],
                    "submission_text": submission_text[:5000],
                    "submitted_at": datetime.now().isoformat(),
                    "is_late": is_late,
                    "days_late": days_late,
                    "status": "late" if is_late else "submitted"
                }).execute()
                
                if result.data:
                    submission_id = result.data[0]["id"]
                    logger.info(f"   ✓ Submission created: {submission_id}")
                else:
                    logger.error("   Submission insert failed - no data returned")
                    return {"status": "error", "message": "Failed to record submission"}
            except Exception as db_error:
                logger.error(f"   ❌ Database insert failed: {str(db_error)}", exc_info=True)
                return {"status": "error", "message": f"Failed to create submission: {str(db_error)}"}

        # Clean up local file
        if os.path.exists(local_file_path):
            os.remove(local_file_path)

        logger.info(f"✅ Assignment submitted successfully")

        return {
            "status": "success",
            "message": "Assignment submitted successfully",
            "submission_id": submission_id,
            "is_late": is_late,
            "days_late": days_late,
            "storage_url": storage_result["storage_url"],
            "storage_path": storage_result["file_path"]
        }

    except HTTPException as he:
        logger.error(f"❌ HTTP Error: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"❌ Submission failed: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📊 VIEW AVAILABLE ASSIGNMENTS
# --------------------------------------------------
@router.get("/assignments")
def get_available_assignments(student_user: dict = Depends(get_current_student)):
    """Get list of all available assignments."""
    try:
        logger.info(f"Fetching available assignments for student")
        
        data = supabase.table("assignments") \
            .select("id, assignment_no, subject, branch, semester, difficulty, given_date, submission_date, created_by, status") \
            .eq("status", "active") \
            .order("created_at", desc=True) \
            .execute()
        
        logger.info(f"✓ Found {len(data.data)} active assignments")
        
        return {
            "status": "success",
            "count": len(data.data),
            "data": data.data
        }
        
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching assignments: {str(e)}")
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📜 VIEW MY SUBMISSIONS
# --------------------------------------------------
@router.get("/my-submissions")
def get_my_submissions(student_user: dict = Depends(get_current_student)):
    """Get all submissions by the student."""
    try:
        # Get student_id from verified user
        student_id = student_user["user_id"]
        
        logger.info(f"Fetching submissions for student: {student_id}")
        
        data = supabase.table("submissions") \
            .select("""
                id,
                assignment_id,
                status,
                is_late,
                days_late,
                submitted_at,
                created_at,
                assignments(assignment_no, subject, submission_date)
            """) \
            .eq("student_id", student_id) \
            .order("created_at", desc=True) \
            .execute()
        
        logger.info(f"✓ Found {len(data.data)} submissions")
        
        return {
            "status": "success",
            "count": len(data.data),
            "data": data.data
        }
        
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching submissions: {str(e)}")
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📋 VIEW SUBMISSION DETAILS
# --------------------------------------------------
@router.get("/submission/{submission_id}")
def get_submission_details(
    submission_id: str,
    student_user: dict = Depends(get_current_student)
):
    """Get detailed information about a specific submission."""
    try:
        # Get student_id from verified user
        student_id = student_user["user_id"]
        
        logger.info(f"Fetching submission details: {submission_id}")
        
        # Get submission
        submission = supabase.table("submissions") \
            .select("*") \
            .eq("id", submission_id) \
            .eq("student_id", student_id) \
            .execute()
        
        if not submission.data:
            logger.warning(f"Submission not found or unauthorized: {submission_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        submission_data = submission.data[0]
        
        # Get evaluation if exists
        evaluation = supabase.table("evaluations") \
            .select("*") \
            .eq("submission_id", submission_id) \
            .execute()
        
        logger.info(f"✓ Retrieved submission details")
        
        return {
            "status": "success",
            "submission": submission_data,
            "evaluation": evaluation.data[0] if evaluation.data else None
        }
        
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching submission: {str(e)}")
        return {"status": "error", "message": str(e)}