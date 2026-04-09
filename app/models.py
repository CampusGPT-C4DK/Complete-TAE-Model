"""
Pydantic models for TAE Model API requests/responses
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID


# ====================================================================
# AUTHENTICATION MODELS
# ====================================================================

class FacultyRegisterRequest(BaseModel):
    """Faculty registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    subject: Optional[str] = "General"

    class Config:
        json_schema_extra = {
            "example": {
                "email": "dr.smith@university.edu",
                "password": "SecurePassword123",
                "full_name": "Dr. John Smith",
                "subject": "Data Structures"
            }
        }


class LoginRequest(BaseModel):
    """Login request for faculty."""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "dr.smith@university.edu",
                "password": "SecurePassword123"
            }
        }


class AuthResponse(BaseModel):
    """Authentication response with tokens."""
    status: str
    message: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_in: Optional[int] = None


# ====================================================================
# ASSIGNMENT MODELS
# ====================================================================

class QuestionData(BaseModel):
    """Single question in an assignment."""
    question_no: int
    question_text: str
    question_type: str  # 'mcq', 'short', 'long', 'essay'
    difficulty: str  # 'easy', 'medium', 'hard'
    marks: int
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "question_no": 1,
                "question_text": "What is binary search?",
                "question_type": "short",
                "difficulty": "medium",
                "marks": 5
            }
        }


class AssignmentGenerateRequest(BaseModel):
    """Request to generate assignment from notes."""
    difficulty: str = Field(..., regex="^(easy|medium|hard)$")
    assignment_no: str
    subject: str
    branch: str
    semester: str
    faculty: str
    given_date: date
    submission_date: date

    class Config:
        json_schema_extra = {
            "example": {
                "difficulty": "medium",
                "assignment_no": "1",
                "subject": "Data Structures",
                "branch": "CSE",
                "semester": "4",
                "faculty": "Dr. Smith",
                "given_date": "2026-04-06",
                "submission_date": "2026-04-13"
            }
        }


class AssignmentResponse(BaseModel):
    """Assignment creation response."""
    status: str
    message: Optional[str] = None
    assignment_id: Optional[str] = None
    pdf_url: Optional[str] = None
    storage_path: Optional[str] = None
    storage_bucket: Optional[str] = None


class AssignmentListItem(BaseModel):
    """Minimal assignment info for list."""
    id: str
    assignment_no: str
    subject: str
    semester: str
    difficulty: str
    given_date: date
    submission_date: date
    pdf_url: str
    created_at: datetime
    total_questions: Optional[int] = None

    class Config:
        from_attributes = True


# ====================================================================
# SUBMISSION MODELS
# ====================================================================

class SubmissionRequest(BaseModel):
    """Student submission."""
    assignment_id: str
    submission_text: Optional[str] = None
    submitted_file_url: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "assignment_id": "uuid-here",
                "submission_text": "My answer text...",
                "submitted_file_url": "https://storage-url/file.pdf"
            }
        }


class SubmissionResponse(BaseModel):
    """Submission creation response."""
    status: str
    submission_id: Optional[str] = None
    submitted_at: Optional[datetime] = None
    is_late: Optional[bool] = None


class SubmissionItem(BaseModel):
    """Submission info for tracking."""
    id: str
    student_id: str
    student_name: Optional[str] = None
    email: Optional[str] = None
    status: str  # 'pending', 'submitted', 'late', 'graded'
    submitted_at: Optional[datetime] = None
    is_late: Optional[bool] = None
    days_late: Optional[int] = None
    marks: Optional[int] = None

    class Config:
        from_attributes = True


# ====================================================================
# EVALUATION MODELS
# ====================================================================

class EvaluationRequest(BaseModel):
    """Evaluation/grading request."""
    submission_id: str
    marks_obtained: int = Field(..., ge=0)
    total_marks: int = 100
    feedback: Optional[str] = None
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "submission_id": "uuid-here",
                "marks_obtained": 85,
                "total_marks": 100,
                "feedback": "Good attempt...",
                "strengths": "Clear logic",
                "areas_for_improvement": "Add more examples"
            }
        }


class EvaluationResponse(BaseModel):
    """Evaluation creation response."""
    status: str
    evaluation_id: Optional[str] = None
    marks_obtained: Optional[int] = None
    percentage: Optional[float] = None
    grade: Optional[str] = None


class EvaluationItem(BaseModel):
    """Evaluation info for tracking."""
    id: str
    submission_id: str
    marks_obtained: int
    total_marks: int
    percentage: float
    grade: str
    feedback: Optional[str] = None
    evaluated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ====================================================================
# DASHBOARD MODELS
# ====================================================================

class AssignmentStats(BaseModel):
    """Statistics for an assignment."""
    id: str
    assignment_no: str
    subject: str
    semester: str
    total_submitted: int
    total_pending: int
    late_submissions: int
    avg_marks: Optional[float] = None
    avg_percentage: Optional[float] = None

    class Config:
        from_attributes = True


class SubmissionStats(BaseModel):
    """Statistics for tracking page."""
    total_assignments: int
    total_graded: int
    avg_percentage: Optional[float] = None
    highest_percentage: Optional[float] = None
    lowest_percentage: Optional[float] = None


# ====================================================================
# ERROR MODELS
# ====================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    status: str = "error"
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class StudentLogin(BaseModel):
    """Legacy model - kept for compatibility."""
    email: str
    password: str