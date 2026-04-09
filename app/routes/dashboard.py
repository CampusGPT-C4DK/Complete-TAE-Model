from fastapi import APIRouter, Header, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from typing import Optional
import logging
from datetime import datetime

from app.database import supabase
from app.services.auth_service import AuthService
from app.core.security import is_student_role, is_faculty_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# HTTPBearer security scheme for Swagger integration
security = HTTPBearer()


# --------------------------------------------------
# 🔐 DEPENDENCY: GET CURRENT USER
# --------------------------------------------------
def get_current_user(credentials = Depends(security)):
    """Extract and verify user from JWT token."""
    try:
        token = credentials.credentials
        logger.info(f"Token received: {token[:50]}...")
        
        # Verify token with Supabase
        user_info = AuthService.verify_token_and_get_user(token)
        logger.info(f"Token verified for user: {user_info.get('user_id')}")
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
# 📊 STUDENT DASHBOARD
# --------------------------------------------------
@router.get("/student-dashboard")
def student_dashboard(user: dict = Depends(get_current_user)):
    """
    Get student's personalized dashboard with submissions and evaluations.
    """
    try:
        # Get user info from verified dependency
        user_info = user
        student_id = user_info["user_id"]
        
        if not is_student_role(user_info.get("role")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This endpoint is for students only"
            )
        
        logger.info(f"Fetching dashboard for student: {student_id}")
        
        # Get all submissions for this student
        submissions = supabase.table("submissions") \
            .select("id, status") \
            .eq("student_id", student_id) \
            .execute()
        
        submission_ids = [s["id"] for s in submissions.data] if submissions.data else []
        
        # Get all evaluations for this student's submissions
        evaluations = []
        if submission_ids:
            evaluations = supabase.table("evaluations") \
                .select("marks_obtained, percentage, grade") \
                .in_("submission_id", submission_ids) \
                .execute()
        
        # Get recent submissions with details
        recent_submissions = supabase.table("submissions") \
            .select("""
                id,
                assignment_id,
                status,
                is_late,
                submitted_at,
                created_at,
                assignments(assignment_no, subject, submission_date)
            """) \
            .eq("student_id", student_id) \
            .order("created_at", desc=True) \
            .limit(5) \
            .execute()
        
        logger.info(f"Processing dashboard data...")
        
        # Calculate statistics
        total_submissions = len(submissions.data)
        graded_count = sum(1 for s in submissions.data if s["status"] == "graded")
        pending_count = sum(1 for s in submissions.data if s["status"] != "graded")
        late_count = sum(1 for s in submissions.data if s.get("is_late", False))
        
        # Calculate grades if available
        avg_marks = None
        avg_percentage = None
        total_grades = None
        
        if evaluations.data:
            marks = [e["marks_obtained"] for e in evaluations.data if e["marks_obtained"] is not None]
            percentages = [e["percentage"] for e in evaluations.data if e["percentage"] is not None]
            
            if marks:
                avg_marks = sum(marks) / len(marks)
            if percentages:
                avg_percentage = sum(percentages) / len(percentages)
            
            total_grades = len(evaluations.data)
        
        logger.info(f"✓ Dashboard data prepared")
        
        return {
            "status": "success",
            "user": {
                "id": student_id,
                "email": user_info.get("email"),
                "full_name": user_info.get("full_name"),
                "role": user_info.get("role")
            },
            "statistics": {
                "total_submissions": total_submissions,
                "graded_submissions": graded_count,
                "pending_submissions": pending_count,
                "late_submissions": late_count,
                "average_marks": round(avg_marks, 2) if avg_marks else None,
                "average_percentage": round(avg_percentage, 2) if avg_percentage else None,
                "total_grades_received": total_grades
            },
            "recent_submissions": recent_submissions.data
        }
        
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching student dashboard: {str(e)}")
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📊 FACULTY DASHBOARD
# --------------------------------------------------
@router.get("/faculty-dashboard")
def faculty_dashboard(user: dict = Depends(get_current_user)):
    """
    Get faculty's dashboard with assignment and evaluation statistics.
    """
    try:
        # Get user info from verified dependency
        user_info = user
        faculty_id = user_info["user_id"]
        
        if not is_faculty_role(user_info.get("role")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This endpoint is for faculty only"
            )
        
        logger.info(f"Fetching dashboard for faculty: {faculty_id}")
        
        # Get all assignments created by this faculty
        assignments = supabase.table("assignments") \
            .select("id, assignment_no, subject, status") \
            .eq("faculty_id", faculty_id) \
            .execute()
        
        assignment_ids = [a["id"] for a in assignments.data]
        
        # Get all submissions for these assignments
        submissions = []
        evaluations = []
        
        if assignment_ids:
            submissions = supabase.table("submissions") \
                .select("id, status, is_late") \
                .in_("assignment_id", assignment_ids) \
                .execute()
            
            evaluations = supabase.table("evaluations") \
                .select("marks_obtained, percentage, grade") \
                .in_("assignment_id", assignment_ids) \
                .execute()
        
        logger.info(f"Processing faculty dashboard data...")
        
        # Calculate statistics
        total_assignments = len(assignments.data)
        active_assignments = sum(1 for a in assignments.data if a["status"] == "active")
        archived_assignments = sum(1 for a in assignments.data if a["status"] == "archived")
        
        total_submissions = len(submissions.data) if submissions.data else 0
        graded_submissions = sum(1 for s in submissions.data if s["status"] == "graded") if submissions.data else 0
        pending_submissions = total_submissions - graded_submissions
        late_submissions = sum(1 for s in submissions.data if s.get("is_late", False)) if submissions.data else 0
        
        # Calculate evaluation metrics
        avg_marks = None
        avg_percentage = None
        
        if evaluations.data:
            marks = [e["marks_obtained"] for e in evaluations.data if e["marks_obtained"] is not None]
            percentages = [e["percentage"] for e in evaluations.data if e["percentage"] is not None]
            
            if marks:
                avg_marks = sum(marks) / len(marks)
            if percentages:
                avg_percentage = sum(percentages) / len(percentages)
        
        # Get recent assignments
        recent_assignments = supabase.table("assignments") \
            .select("id, assignment_no, subject, branch, semester, created_at") \
            .eq("faculty_id", faculty_id) \
            .order("created_at", desc=True) \
            .limit(5) \
            .execute()
        
        # Get pending submissions count per assignment
        pending_by_assignment = {}
        if assignment_ids:
            for assignment_id in assignment_ids:
                pending = supabase.table("submissions") \
                    .select("id") \
                    .eq("assignment_id", assignment_id) \
                    .neq("status", "graded") \
                    .execute()
                
                pending_by_assignment[assignment_id] = len(pending.data) if pending.data else 0
        
        logger.info(f"✓ Faculty dashboard data prepared")
        
        return {
            "status": "success",
            "user": {
                "id": faculty_id,
                "email": user_info.get("email"),
                "full_name": user_info.get("full_name"),
                "role": user_info.get("role")
            },
            "assignment_statistics": {
                "total_assignments": total_assignments,
                "active_assignments": active_assignments,
                "archived_assignments": archived_assignments
            },
            "submission_statistics": {
                "total_submissions": total_submissions,
                "graded_submissions": graded_submissions,
                "pending_submissions": pending_submissions,
                "late_submissions": late_submissions
            },
            "evaluation_metrics": {
                "average_marks": round(avg_marks, 2) if avg_marks else None,
                "average_percentage": round(avg_percentage, 2) if avg_percentage else None,
                "total_evaluations": len(evaluations.data) if evaluations.data else 0
            },
            "recent_assignments": recent_assignments.data,
            "pending_by_assignment": pending_by_assignment
        }
        
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching faculty dashboard: {str(e)}")
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📚 STUDENT PERFORMANCE ANALYTICS
# --------------------------------------------------
@router.get("/student-performance")
def student_performance(user: dict = Depends(get_current_user)):
    """
    Get comprehensive student performance analytics.
    """
    try:
        # Get user info from verified dependency
        user_info = user
        student_id = user_info["user_id"]
        
        if not is_student_role(user_info.get("role")):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This endpoint is for students only"
            )
        
        logger.info(f"Fetching performance analytics for student: {student_id}")
        
        # Get all submissions for this student
        submissions = supabase.table("submissions") \
            .select("id") \
            .eq("student_id", student_id) \
            .execute()
        
        submission_ids = [s["id"] for s in submissions.data] if submissions.data else []
        
        # Get all evaluations for this student's submissions
        evaluations = []
        if submission_ids:
            evaluations = supabase.table("evaluations") \
                .select("""
                    id,
                    assignment_id,
                    marks_obtained,
                    percentage,
                    grade,
                    evaluated_at,
                    assignments(assignment_no, subject)
                """) \
                .in_("submission_id", submission_ids) \
                .order("evaluated_at", desc=True) \
                .execute()
        
        logger.info(f"Processing {len(evaluations.data)} evaluations...")
        
        # Organize by subject
        by_subject = {}
        
        if evaluations.data:
            for eval_data in evaluations.data:
                subject = eval_data.get("assignments", {}).get("subject", "Unknown")
                
                if subject not in by_subject:
                    by_subject[subject] = {
                        "evaluations": [],
                        "average_percentage": 0,
                        "average_marks": 0,
                        "total": 0
                    }
                
                by_subject[subject]["evaluations"].append(eval_data)
            
            # Calculate per-subject stats
            for subject, data in by_subject.items():
                evals = data["evaluations"]
                percentages = [e["percentage"] for e in evals if e["percentage"] is not None]
                marks = [e["marks_obtained"] for e in evals if e["marks_obtained"] is not None]
                
                if percentages:
                    data["average_percentage"] = round(sum(percentages) / len(percentages), 2)
                if marks:
                    data["average_marks"] = round(sum(marks) / len(marks), 2)
                
                data["total"] = len(evals)
        
        logger.info(f"✓ Performance analytics prepared")
        
        return {
            "status": "success",
            "performance_by_subject": by_subject,
            "total_evaluations": len(evaluations.data) if evaluations.data else 0
        }
        
    except HTTPException as he:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching performance analytics: {str(e)}")
        return {"status": "error", "message": str(e)}