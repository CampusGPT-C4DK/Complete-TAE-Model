from fastapi import FastAPI
from app.routes import teacher, student, evaluation

app = FastAPI(title="EduGenAI")

app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(evaluation.router)

@app.get("/")
def home():
    return {"message": "EduGenAI Running 🚀"}

from app.routes import dashboard

app.include_router(dashboard.router)