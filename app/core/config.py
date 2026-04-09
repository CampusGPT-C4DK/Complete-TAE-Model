"""
TAE Model Configuration
Uses Pydantic settings for robust environment variable loading.
Validates all critical credentials on startup.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Get the tae_model directory (parent of app/core)
TAE_MODEL_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = ConfigDict(
        env_file=str(TAE_MODEL_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        str_strip_whitespace=True
    )

    # App Settings
    APP_NAME: str = "EduGenAI"
    APP_VERSION: str = "1.0"
    DEBUG: bool = Field(default=False)

    # Supabase Configuration - CRITICAL: Must match backend
    SUPABASE_URL: str = Field(default="", description="Supabase project URL")
    SUPABASE_KEY: str = Field(default="", description="Supabase anon key")
    SUPABASE_SERVICE_KEY: str = Field(default="", description="Supabase service role key")
    SUPABASE_JWT_SECRET: str = Field(default="", description="Supabase JWT secret for token verification")

    # LLM Model Configuration
    USE_PHI3_MINI: bool = Field(default=False, description="Enable phi3:mini local model")
    USE_GEMINI: bool = Field(default=True, description="Enable Google Gemini API")
    USE_MISTRAL: bool = Field(default=False, description="Enable mistral:7b-instruct local model")

    # Ollama Configuration (for local models)
    OLLAMA_HOST: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="phi3:mini")

    # Google Gemini Configuration
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash", description="Gemini model version")

    # Mistral Configuration
    MISTRAL_API_KEY: Optional[str] = Field(default=None, description="Mistral API key")

    # Storage Configuration
    STORAGE_ENABLED: bool = Field(default=True)
    TEACHER_NOTES_BUCKET: str = Field(default="teacher-notes")
    ASSIGNMENTS_BUCKET: str = Field(default="assignments")

    def validate_supabase_credentials(self) -> None:
        """
        Validate that all critical Supabase credentials are present.
        Raises ValueError if any are missing.
        """
        missing = []
        
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        if not self.SUPABASE_SERVICE_KEY:
            missing.append("SUPABASE_SERVICE_KEY")
        if not self.SUPABASE_JWT_SECRET:
            missing.append("SUPABASE_JWT_SECRET")
        
        if missing:
            raise ValueError(
                f"❌ Missing Supabase credentials in .env:\n"
                f"   {', '.join(missing)}\n"
                f"Copy these from backend/.env to tae_model/.env:\n"
                f"   - SUPABASE_URL\n"
                f"   - SUPABASE_KEY\n"
                f"   - SUPABASE_SERVICE_KEY\n"
                f"   - SUPABASE_JWT_SECRET"
            )
        
        logger.info("✅ Supabase credentials loaded successfully")

    def validate_llm_selection(self) -> None:
        """Validate exactly ONE LLM provider is enabled."""
        enabled_count = sum([self.USE_PHI3_MINI, self.USE_GEMINI, self.USE_MISTRAL])
        
        if enabled_count == 0:
            raise ValueError(
                "❌ No LLM provider enabled! Set ONE in .env:\n"
                "   USE_PHI3_MINI=true (or)\n"
                "   USE_GEMINI=true (or)\n"
                "   USE_MISTRAL=true"
            )
        if enabled_count > 1:
            raise ValueError(
                "❌ Multiple LLM providers enabled! Set EXACTLY ONE in .env"
            )
        
        logger.info(f"✅ LLM provider: {'phi3:mini' if self.USE_PHI3_MINI else 'Gemini' if self.USE_GEMINI else 'Mistral'}")


# Global settings instance
settings = Settings()

# Validate on startup
try:
    settings.validate_supabase_credentials()
    settings.validate_llm_selection()
except ValueError as e:
    logger.error(str(e))
    raise
