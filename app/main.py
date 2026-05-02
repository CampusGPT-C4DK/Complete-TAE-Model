import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import teacher, student, evaluation, dashboard
from app.core.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate configuration on startup
logger.info("Starting TAE Model (EduGenAI)...")
logger.info(f"Supabase URL: {settings.SUPABASE_URL}")
logger.info(f"Service Role Key configured: {'✓' if settings.SUPABASE_SERVICE_KEY else '✗'}")
logger.info(f"JWT Secret configured: {'✓' if settings.SUPABASE_JWT_SECRET else '✗'}")

app = FastAPI(title="EduGenAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(evaluation.router)
app.include_router(dashboard.router)

@app.get("/")
def home():
    return {"message": "EduGenAI Running 🚀", "version": settings.APP_VERSION}

@app.get("/health")
def health_check():
    """Health check endpoint - verifies Supabase connection."""
    return {
        "status": "healthy",
        "service": "EduGenAI",
        "supabase_configured": bool(settings.SUPABASE_URL and settings.SUPABASE_KEY),
        "jwt_secret_configured": bool(settings.SUPABASE_JWT_SECRET)
    }