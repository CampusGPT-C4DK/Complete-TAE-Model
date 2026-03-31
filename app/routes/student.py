from fastapi import APIRouter, UploadFile, File, Form
import shutil
import os
import hashlib
from datetime import datetime

from app.database import supabase
from app.models import StudentLogin

from app.services.pdf_processor import extract_text
from app.services.semantic_similarity import semantic_similarity
from app.services.report_generator import generate_report

router = APIRouter(prefix="/student", tags=["Student"])


# --------------------------------------------------
# 📝 STUDENT REGISTER
# --------------------------------------------------
@router.post("/register")
def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    branch: str = Form(...),
    semester: str = Form(...)
):
    try:
        # Check existing user
        existing = supabase.table("students") \
            .select("*") \
            .eq("email", email) \
            .execute()

        if existing.data:
            return {"status": "error", "message": "User already exists"}

        # Hash password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Insert student
        user = supabase.table("students").insert({
            "name": name,
            "email": email,
            "password": hashed_password,
            "branch": branch,
            "semester": semester
        }).execute()

        return {
            "status": "success",
            "student_id": user.data[0]["id"],
            "message": "Account created successfully"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 🔐 STUDENT LOGIN
# --------------------------------------------------
@router.post("/login")
def login(data: StudentLogin):
    try:
        hashed_password = hashlib.sha256(data.password.encode()).hexdigest()

        user = supabase.table("students") \
            .select("*") \
            .eq("email", data.email) \
            .eq("password", hashed_password) \
            .execute()

        if not user.data:
            return {"status": "error", "message": "Invalid credentials"}

        return {
            "status": "success",
            "student_id": user.data[0]["id"],
            "name": user.data[0]["name"]
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📤 SUBMIT ASSIGNMENT
# --------------------------------------------------
@router.post("/submit-assignment")
async def submit_assignment(
    student_id: str = Form(...),
    assignment_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # -------------------------------
        # 1. Validate File
        # -------------------------------
        if not file.filename.endswith(".pdf"):
            return {"status": "error", "message": "Only PDF files allowed"}

        os.makedirs("student_uploads", exist_ok=True)

        file_path = f"student_uploads/{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # -------------------------------
        # 2. Extract Text (FIXED)
        # -------------------------------
        student_text = extract_text(file_path)

        if not student_text:
            return {"status": "error", "message": "Failed to extract text"}

        # -------------------------------
        # 3. Get Assignment Data
        # -------------------------------
        assignment = supabase.table("assignments") \
            .select("*") \
            .eq("id", assignment_id) \
            .execute()

        if not assignment.data:
            return {"status": "error", "message": "Assignment not found"}

        assignment_data = assignment.data[0]
        notes_text = assignment_data["generated_assignment"]

        # Fix date format
        submission_deadline = assignment_data["submission_date"]
        if isinstance(submission_deadline, str):
            submission_deadline = datetime.strptime(submission_deadline, "%Y-%m-%d").date()

        # -------------------------------
        # 4. Late Submission Logic
        # -------------------------------
        today = datetime.now().date()
        late_days = max(0, (today - submission_deadline).days)

        if late_days == 0:
            late_marks = 3
        elif late_days == 1:
            late_marks = 2
        elif late_days == 2:
            late_marks = 1
        elif late_days == 3:
            late_marks = 0
        else:
            return {
                "status": "failed",
                "message": "Submission too late (more than 3 days)"
            }

        # -------------------------------
        # 5. Save Submission
        # -------------------------------
        submission = supabase.table("submissions").insert({
            "student_id": student_id,
            "assignment_id": assignment_id,
            "submission_text": student_text[:10000],
            "file_path": file_path,
            "created_at": str(datetime.now())
        }).execute()

        if not submission.data:
            return {"status": "error", "message": "Submission insert failed"}

        submission_id = submission.data[0]["id"]

        # -------------------------------
        # 6. Similarity (INFO ONLY)
        # -------------------------------
        similarity = semantic_similarity(notes_text, student_text)
        similarity_marks = round((1 - similarity / 100) * 7, 2)

        # -------------------------------
        # 7. FINAL MARKS (ONLY LATE MARKS)
        # -------------------------------
        final_marks = late_marks

        # -------------------------------
        # 8. Generate Report
        # -------------------------------
        report_path = generate_report(
            student_id,
            final_marks,
            "Evaluation Completed"
        )

        # -------------------------------
        # 9. Save Evaluation
        # -------------------------------
        eval_insert = supabase.table("evaluations").insert({
            "evaluation_result": "Evaluation Completed",
            "report_path": report_path,
            "similarity": similarity,
            "submission_status": "evaluated",
            "late_days": late_days,
            "submission_marks": similarity_marks,
            "late_marks": late_marks,
            "final_marks": final_marks,
            "student_id": student_id,
            "assignment_id": assignment_id,
            "submitted_at": str(today)
        }).execute()

        if not eval_insert.data:
            return {"status": "error", "message": "Evaluation insert failed"}

        # -------------------------------
        # 10. Response
        # -------------------------------
        return {
            "status": "success",
            "submission_id": submission_id,
            "similarity": similarity,
            "similarity_marks": similarity_marks,
            "obtained_marks": late_marks,
            "final_marks": final_marks,
            "report": report_path
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📊 STUDENT DASHBOARD
# --------------------------------------------------
@router.get("/dashboard/{student_id}")
def student_dashboard(student_id: str):
    try:
        data = supabase.table("evaluations") \
            .select("""
                final_marks,
                submission_status,
                assignments(subject, assignment_no)
            """) \
            .eq("student_id", student_id) \
            .execute()

        return {
            "status": "success",
            "data": data.data
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}