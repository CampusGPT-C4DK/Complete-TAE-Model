"""
Security module for token verification and password operations.
Uses Supabase JWT tokens.
"""

import logging
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")


def verify_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Supabase JWT token (basic validation).
    
    Args:
        token: JWT token string
    
    Returns:
        Dict with token payload or None if invalid
    """
    try:
        # For production, use JWT verification library
        # This is a basic implementation
        if not token:
            logger.warning("Empty token")
            return None
        
        # Supabase tokens are typically longer than 50 chars
        if len(token) < 50:
            logger.warning("Invalid token format")
            return None
        
        logger.info("✓ Token format valid")
        return {"valid": True}
        
    except Exception as e:
        logger.error(f"❌ Token verification failed: {str(e)}")
        return None


def is_faculty_role(role: str) -> bool:
    """Check if user has faculty role."""
    return role in ["faculty", "admin"]


def is_admin_role(role: str) -> bool:
    """Check if user has admin role."""
    return role == "admin"


def is_student_role(role: str) -> bool:
    """Check if user has student role."""
    return role == "student"
