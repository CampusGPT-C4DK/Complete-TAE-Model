from fastapi import APIRouter
from app.database import supabase

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/performance")
def student_performance():

    data = supabase.table("evaluations").select("*").execute()

    similarities = []

    for row in data.data:
        if row["similarity"] is not None:
            similarities.append(row["similarity"])

    avg_similarity = sum(similarities)/len(similarities) if similarities else 0

    return {
        "total_submissions": len(data.data),
        "average_similarity": avg_similarity
    }