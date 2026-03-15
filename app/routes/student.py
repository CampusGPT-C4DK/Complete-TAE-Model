from fastapi import APIRouter, UploadFile, File
import shutil

from app.services.pdf_processor import extract_text
from app.services.assignment_validator import validate_assignment
from app.services.semantic_similarity import semantic_similarity
from app.services.report_generator import generate_report

from app.database import supabase

router = APIRouter(prefix="/student", tags=["Student"])


@router.post("/submit-assignment")
async def submit_assignment(file: UploadFile = File(...)):

    path = f"uploads/{file.filename}"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    student_text = extract_text(path)

    notes = supabase.table("assignments").select("*").order("id", desc=True).limit(1).execute()

    notes_text = notes.data[0]["generated_assignment"]

    evaluation = validate_assignment(notes_text, student_text)

    similarity = semantic_similarity(notes_text, student_text)

    score = 8
    feedback = evaluation

    report = generate_report("Student", score, feedback)

    supabase.table("evaluations").insert({
        "evaluation_result": evaluation,
        "similarity": similarity,
        "report_path": report
    }).execute()

    return {
        "evaluation": evaluation,
        "similarity": similarity,
        "report": report
    }