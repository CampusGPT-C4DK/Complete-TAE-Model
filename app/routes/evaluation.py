from fastapi import APIRouter
from app.services.assignment_validator import validate_assignment

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])

@router.post("/validate")
def validate(data: dict):

    result = evaluate(
        data["student_text"],
        data["reference"]
    )

    return {"result": result}