import logging
from supabase import create_client
from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------
# READ VARIABLES FROM PYDANTIC SETTINGS
# ---------------------------------------------------
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY  # Anon key
SERVICE_ROLE_KEY = settings.SUPABASE_SERVICE_KEY  # Service role key

logger.info(f"Loading Supabase credentials...")
logger.info(f"  URL: {SUPABASE_URL}")
logger.info(f"  Anon key: {SUPABASE_KEY[:20]}...")
if SERVICE_ROLE_KEY:
    logger.info(f"  Service role key: ✓ Available")
else:
    logger.warning(f"  Service role key: ✗ Missing - some admin operations will fail")

# ---------------------------------------------------
# VALIDATE (Config already validates in core/config.py)
# ---------------------------------------------------
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "❌ Supabase credentials not found.\n"
        "Check your .env file contains:\n"
        "SUPABASE_URL=...\n"
        "SUPABASE_KEY=..."
    )

# ---------------------------------------------------
# CREATE CLIENTS
# ---------------------------------------------------
# Anon key client (for regular users)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
logger.info("✅ Supabase anon client initialized")

# Service role client (for admin operations, bypasses RLS)
# Only create if SERVICE_ROLE_KEY is available
supabase_admin = None
if SERVICE_ROLE_KEY:
    supabase_admin = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
    logger.info("✅ Supabase service role client initialized")
else:
    logger.warning("⚠️  SERVICE_ROLE_KEY not configured. Some admin operations may fail.")