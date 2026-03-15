from fastapi import APIRouter, UploadFile, File, Form
from typing import List

from app.services.pdf_processor import extract_text
from app.services.assignment_generator import generate_questions
from app.services.assignment_pdf import generate_assignment_pdf

router = APIRouter()


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
        submission_date: str = Form(...)
):

    unit_notes = {}

    for i, file in enumerate(files):

        text = extract_text(file)

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
        given_date,
        submission_date
    )

    return {
        "status": "success",
        "pdf": pdf_path,
        "questions": questions
    }