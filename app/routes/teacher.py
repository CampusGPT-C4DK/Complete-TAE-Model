from fastapi import APIRouter, UploadFile, File, Form
from typing import List
import os
import pandas as pd
import hashlib
from datetime import datetime

from app.database import supabase

from app.services.pdf_processor import extract_text
from app.services.assignment_generator import generate_questions
from app.services.assignment_pdf import generate_assignment_pdf

router = APIRouter(prefix="/teacher", tags=["Teacher"])


# --------------------------------------------------
# 📅 DATE FORMAT HANDLER
# --------------------------------------------------
def format_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        try:
            return datetime.strptime(date_str, "%d-%m-%Y").date()
        except:
            return datetime.strptime(date_str, "%d/%m/%Y").date()


# --------------------------------------------------
# 📝 TEACHER REGISTER
# --------------------------------------------------
@router.post("/register")
def register_teacher(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    subject: str = Form(...)
):
    try:
        existing = supabase.table("teachers") \
            .select("*") \
            .eq("email", email) \
            .execute()

        if existing.data:
            return {"status": "error", "message": "Teacher already exists"}

        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        teacher = supabase.table("teachers").insert({
            "name": name,
            "email": email,
            "password": hashed_password,
            "subject": subject
        }).execute()

        return {
            "status": "success",
            "teacher_id": teacher.data[0]["id"]
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 🔐 TEACHER LOGIN
# --------------------------------------------------
@router.post("/login")
def login_teacher(email: str = Form(...), password: str = Form(...)):
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        teacher = supabase.table("teachers") \
            .select("*") \
            .eq("email", email) \
            .eq("password", hashed_password) \
            .execute()

        if not teacher.data:
            return {"status": "error", "message": "Invalid credentials"}

        return {
            "status": "success",
            "teacher_id": teacher.data[0]["id"],
            "name": teacher.data[0]["name"]
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📤 UPLOAD NOTES & GENERATE ASSIGNMENT
# --------------------------------------------------
@router.post("/upload-notes")
async def upload_notes(
    teacher_id: str = Form(...),
    files: List[UploadFile] = File(...),
    difficulty: str = Form(...),
    assignment_no: str = Form(...),
    subject: str = Form(...),
    branch: str = Form(...),
    semester: str = Form(...),
    faculty: str = Form(...),
    given_date: str = Form(...),
    submission_date: str = Form(...)
):
    try:
        given_date = format_date(given_date)
        submission_date = format_date(submission_date)

        os.makedirs("teacher_uploads", exist_ok=True)

        unit_notes = {}

        for i, file in enumerate(files):
            file_path = f"teacher_uploads/{file.filename}"

            with open(file_path, "wb") as buffer:
                buffer.write(file.file.read())

            text = extract_text(file_path)

            if not text:
                return {
                    "status": "error",
                    "message": f"Extraction failed for {file.filename}"
                }

            unit_notes[f"Unit {i+1}"] = text

        questions = generate_questions(unit_notes, difficulty)

        pdf_path = generate_assignment_pdf(
            questions,
            assignment_no,
            subject,
            branch,
            semester,
            "Multiple Units",
            faculty,
            str(given_date),
            str(submission_date)
        )

        assignment = supabase.table("assignments").insert({
            "generated_assignment": str(questions)[:5000],
            "assignment_no": assignment_no,
            "subject": subject,
            "branch": branch,
            "semester": semester,
            "faculty": faculty,
            "given_date": str(given_date),
            "submission_date": str(submission_date),
            "pdf_path": pdf_path,
            "teacher_id": teacher_id
        }).execute()

        if not assignment.data:
            return {"status": "error", "message": "Insert failed"}

        return {
            "status": "success",
            "assignment_id": assignment.data[0]["id"],
            "pdf": pdf_path
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📚 VIEW MY ASSIGNMENTS
# --------------------------------------------------
@router.get("/my-assignments/{teacher_id}")
def get_assignments(teacher_id: str):
    try:
        data = supabase.table("assignments") \
            .select("*") \
            .eq("teacher_id", teacher_id) \
            .execute()

        return {"status": "success", "data": data.data}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📊 TRACK SUBMISSIONS (PER ASSIGNMENT)
# --------------------------------------------------
@router.get("/track-submissions/{assignment_id}")
def track_submissions(assignment_id: str):
    try:
        data = supabase.table("evaluations") \
            .select("""
                final_marks,
                late_days,
                submission_status,
                students(name, email)
            """) \
            .eq("assignment_id", assignment_id) \
            .execute()

        formatted = []

        for row in data.data:
            formatted.append({
                "student_name": row.get("students", {}).get("name"),
                "email": row.get("students", {}).get("email"),
                "marks": row.get("final_marks"),
                "late_days": row.get("late_days"),
                "status": row.get("submission_status")
            })

        return {"status": "success", "data": formatted}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📊 ALL SUBMISSIONS (ALL ASSIGNMENTS)
# --------------------------------------------------
@router.get("/all-submissions")
def all_submissions():
    try:
        data = supabase.table("evaluations") \
            .select("""
                final_marks,
                late_days,
                submission_status,
                students(name),
                assignments(assignment_no, subject)
            """) \
            .execute()

        return {"status": "success", "data": data.data}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📊 DASHBOARD
# --------------------------------------------------
@router.get("/dashboard")
def teacher_dashboard():
    try:
        data = supabase.table("evaluations") \
            .select("""
                final_marks,
                submission_status,
                late_days,
                students(name),
                assignments(subject, assignment_no)
            """) \
            .execute()

        return {"status": "success", "data": data.data}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --------------------------------------------------
# 📥 EXPORT TO EXCEL
# --------------------------------------------------
@router.get("/export-excel")
def export_excel():
    try:
        data = supabase.table("evaluations") \
            .select("*") \
            .execute()

        df = pd.DataFrame(data.data)

        os.makedirs("reports", exist_ok=True)
        file_path = "reports/teacher_dashboard.xlsx"

        df.to_excel(file_path, index=False)

        return {"status": "success", "file": file_path}

    except Exception as e:
        return {"status": "error", "message": str(e)}