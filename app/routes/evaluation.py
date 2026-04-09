from fastapi import APIRouter, Header, HTTPException, status, Form, Depends
from fastapi.security import HTTPBearer
from typing import Optional, List, Dict, Any
import logging
import json
from datetime import datetime

from app.database import supabase, supabase_admin
from app.services.auth_service import AuthService
from app.core.security import is_faculty_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/evaluation", tags=["Evaluation"])

# HTTPBearer security scheme for Swagger integration
security = HTTPBearer()


# --------------------------------------------------
# 🔐 DEPENDENCY: GET CURRENT FACULTY USER
# --------------------------------------------------
def get_current_faculty(credentials = Depends(security)):
    """Extract and verify faculty user from JWT token."""
    try:
        token = credentials.credentials
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
# 📋 GET PENDING SUBMISSIONS FOR FACULTY
# --------------------------------------------------
@router.get("/pending-submissions")
def get_pending_submissions(faculty_user: dict = Depends(get_current_faculty)):
    """
    Get all pending submissions for the faculty's assignments.
    Faculty can only see their own assignments.
    """
    try:
        # Get faculty_id from verified user
        faculty_id = faculty_user["user_id"]
        
        logger.info(f"Fetching pending submissions for faculty: {faculty_id}")
        
        # Get all assignments by this faculty
        assignments = supabase.table("assignments") \
            .select("id") \
            .eq("faculty_id", faculty_id) \
            .execute()
        
        assignment_ids = [a["id"] for a in assignments.data]
        
        if not assignment_ids:
            logger.info("No assignments found for this faculty")
            return {
                "status": "success",
                "count": 0,
                "data": []
            }
        
        # Get pending submissions for these assignments
        submissions = supabase.table("submissions") \
            .select("""
                id,
                assignment_id,
                student_id,
                status,
                is_late,
                days_late,
                submitted_at,
                submitted_file_url,
                assignments(assignment_no, subject, submission_date),
                user_profiles!student_id(email, full_name)
            """) \
            .in_("assignment_id", assignment_ids) \
            .neq("status", "graded") \
            .order("submitted_at", desc=True) \
            .execute()
        
        logger.info(f"✓ Found {len(submissions.data)} pending submissions")
        
        return {
            "status": "success",
            "count": len(submissions.data),
            "data": submissions.data
        }
        
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching pending submissions: {str(e)}")
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📊 GET SUBMISSION DETAILS FOR GRADING
# --------------------------------------------------
@router.get("/submission/{submission_id}")
def get_submission_for_grading(
    submission_id: str,
    faculty_user: dict = Depends(get_current_faculty)
):
    """
    Get detailed submission information for grading.
    Faculty can only see submissions for their assignments.
    """
    try:
        # Get faculty_id from verified user
        faculty_id = faculty_user["user_id"]
        
        logger.info(f"Fetching submission details: {submission_id}")
        
        # Get submission with assignment and student info
        submission = supabase.table("submissions") \
            .select("""
                id,
                assignment_id,
                student_id,
                submitted_file_url,
                submission_text,
                submitted_at,
                is_late,
                days_late,
                status,
                assignments(
                    id,
                    assignment_no,
                    subject,
                    difficulty,
                    total_questions,
                    pdf_url,
                    faculty_id
                ),
                user_profiles!student_id(email, full_name)
            """) \
            .eq("id", submission_id) \
            .execute()
        
        if not submission.data:
            logger.warning(f"Submission not found: {submission_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        submission_data = submission.data[0]
        
        # Check if this faculty owns the assignment
        if submission_data["assignments"]["faculty_id"] != faculty_id:
            logger.warning(f"Faculty {faculty_id} trying to access submission from another faculty")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to grade this submission"
            )
        
        # Get any existing evaluation
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


# --------------------------------------------------
# ✅ GRADE SUBMISSION
# --------------------------------------------------
@router.post("/grade-submission")
def grade_submission(
    submission_id: str = Form(...),
    total_marks: int = Form(...),
    marks_obtained: int = Form(...),
    grade: str = Form(...),
    feedback: str = Form(default=""),
    strengths: str = Form(default=""),
    areas_for_improvement: str = Form(default=""),
    model_evaluation: str = Form(default=""),
    faculty_user: dict = Depends(get_current_faculty)
):
    """
    Grade a student submission and create evaluation record.
    Faculty can only grade submissions for their assignments.
    """
    try:
        # Get faculty_id from verified user
        faculty_id = faculty_user["user_id"]
        
        logger.info(f"Faculty {faculty_id} grading submission: {submission_id}")
        
        # Get submission data
        submission = supabase.table("submissions") \
            .select("assignment_id, student_id, status") \
            .eq("id", submission_id) \
            .execute()
        
        if not submission.data:
            logger.warning(f"Submission not found: {submission_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        submission_data = submission.data[0]
        assignment_id = submission_data["assignment_id"]
        student_id = submission_data["student_id"]
        
        # Verify faculty owns this assignment
        assignment = supabase.table("assignments") \
            .select("faculty_id") \
            .eq("id", assignment_id) \
            .execute()
        
        if not assignment.data or assignment.data[0]["faculty_id"] != faculty_id:
            logger.warning(f"Faculty {faculty_id} trying to grade submission from another faculty")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to grade this submission"
            )
        
        # Validate marks
        if marks_obtained > total_marks or marks_obtained < 0:
            logger.warning(f"Invalid marks: {marks_obtained}/{total_marks}")
            return {"status": "error", "message": "Marks obtained cannot be greater than total marks"}
        
        # Calculate percentage
        percentage = (marks_obtained / total_marks * 100) if total_marks > 0 else 0
        
        # Check if evaluation exists
        existing_eval = supabase.table("evaluations") \
            .select("id") \
            .eq("submission_id", submission_id) \
            .execute()
        
        logger.info(f"   Calculating percentage: {percentage:.2f}%")
        
        if existing_eval.data:
            # Update existing evaluation
            logger.info(f"   Updating existing evaluation...")
            eval_id = existing_eval.data[0]["id"]
            
            db_client = supabase_admin if supabase_admin else supabase
            result = db_client.table("evaluations").update({
                "total_marks": total_marks,
                "marks_obtained": marks_obtained,
                "percentage": percentage,
                "grade": grade,
                "feedback": feedback,
                "strengths": strengths,
                "areas_for_improvement": areas_for_improvement,
                "model_evaluation": model_evaluation,
                "evaluated_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }).eq("id", eval_id).execute()
            
            logger.info(f"   ✓ Evaluation updated")
        else:
            # Create new evaluation
            logger.info(f"   Creating new evaluation...")
            db_client = supabase_admin if supabase_admin else supabase
            result = db_client.table("evaluations").insert({
                "submission_id": submission_id,
                "assignment_id": assignment_id,
                "faculty_id": faculty_id,
                "total_marks": total_marks,
                "marks_obtained": marks_obtained,
                "percentage": percentage,
                "grade": grade,
                "feedback": feedback,
                "strengths": strengths,
                "areas_for_improvement": areas_for_improvement,
                "model_evaluation": model_evaluation,
                "evaluated_at": datetime.now().isoformat()
            }).execute()
            
            if not result.data:
                logger.error("Evaluation insert failed")
                return {"status": "error", "message": "Failed to create evaluation"}
            
            logger.info(f"   ✓ Evaluation created")
        
        # Update submission status to graded
        logger.info(f"   Updating submission status to graded...")
        db_client = supabase_admin if supabase_admin else supabase
        db_client.table("submissions").update({
            "status": "graded",
            "updated_at": datetime.now().isoformat()
        }).eq("id", submission_id).execute()
        
        logger.info(f"✅ Submission graded successfully")
        
        return {
            "status": "success",
            "message": "Submission graded successfully",
            "submission_id": submission_id,
            "marks_obtained": marks_obtained,
            "percentage": round(percentage, 2),
            "grade": grade
        }
        
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"❌ Grading failed: {str(e)}")
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📈 GET EVALUATION RESULTS FOR STUDENT
# --------------------------------------------------
@router.get("/results/{submission_id}")
def get_evaluation_results(submission_id: str):
    """
    Get evaluation results for a submission.
    Public endpoint - anyone can view results with submission ID.
    """
    try:
        logger.info(f"Fetching evaluation results: {submission_id}")
        
        # Get submission to verify student
        submission = supabase.table("submissions") \
            .select("student_id, status") \
            .eq("id", submission_id) \
            .execute()
        
        if not submission.data:
            logger.warning(f"Submission not found: {submission_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submission not found"
            )
        
        # Get evaluation details
        evaluation = supabase.table("evaluations") \
            .select("""
                id,
                total_marks,
                marks_obtained,
                percentage,
                grade,
                feedback,
                strengths,
                areas_for_improvement,
                model_evaluation,
                evaluated_at,
                user_profiles!faculty_id(full_name)
            """) \
            .eq("submission_id", submission_id) \
            .execute()
        
        if not evaluation.data:
            logger.warning(f"Evaluation not found for submission: {submission_id}")
            return {
                "status": "not_evaluated",
                "message": "This submission has not been evaluated yet"
            }
        
        logger.info(f"✓ Retrieved evaluation results")
        
        return {
            "status": "success",
            "evaluation": evaluation.data[0]
        }
        
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching evaluation: {str(e)}")
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 🔍 GET GRADING STATISTICS FOR ASSIGNMENT
# --------------------------------------------------
@router.get("/assignment-stats/{assignment_id}")
def get_assignment_grading_stats(
    assignment_id: str,
    faculty_user: dict = Depends(get_current_faculty)
):
    """
    Get grading statistics for an assignment.
    Faculty can only see stats for their assignments.
    """
    try:
        # Get faculty_id from verified user
        faculty_id = faculty_user["user_id"]
        
        logger.info(f"Fetching grading stats for assignment: {assignment_id}")
        
        # Verify faculty owns this assignment
        assignment = supabase.table("assignments") \
            .select("faculty_id") \
            .eq("id", assignment_id) \
            .execute()
        
        if not assignment.data or assignment.data[0]["faculty_id"] != faculty_id:
            logger.warning(f"Faculty {faculty_id} trying to access stats from another faculty")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this data"
            )
        
        # Get submission statistics
        submissions = supabase.table("submissions") \
            .select("status") \
            .eq("assignment_id", assignment_id) \
            .execute()
        
        # Get evaluation statistics
        evaluations = supabase.table("evaluations") \
            .select("marks_obtained, percentage, grade") \
            .eq("assignment_id", assignment_id) \
            .execute()
        
        logger.info(f"Processing stats...")
        
        # Calculate stats
        total_submissions = len(submissions.data)
        graded_count = sum(1 for s in submissions.data if s["status"] == "graded")
        pending_count = total_submissions - graded_count
        late_count = sum(1 for s in submissions.data if s.get("is_late", False))
        
        avg_marks = None
        avg_percentage = None
        
        if evaluations.data:
            marks = [e["marks_obtained"] for e in evaluations.data if e["marks_obtained"] is not None]
            percentages = [e["percentage"] for e in evaluations.data if e["percentage"] is not None]
            
            if marks:
                avg_marks = sum(marks) / len(marks)
            if percentages:
                avg_percentage = sum(percentages) / len(percentages)
        
        logger.info(f"✓ Calculated stats")
        
        return {
            "status": "success",
            "assignment_id": assignment_id,
            "total_submissions": total_submissions,
            "graded_submissions": graded_count,
            "pending_submissions": pending_count,
            "late_submissions": late_count,
            "average_marks": round(avg_marks, 2) if avg_marks else None,
            "average_percentage": round(avg_percentage, 2) if avg_percentage else None
        }
        
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching stats: {str(e)}")
        return {"status": "error", "message": str(e)}