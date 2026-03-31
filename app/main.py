from fastapi import FastAPI
from app.routes import teacher, student, evaluation, dashboard

app = FastAPI(title="EduGenAI")

app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(evaluation.router)
app.include_router(dashboard.router)

@app.get("/")
def home():
    return {"message": "EduGenAI Running 🚀"}