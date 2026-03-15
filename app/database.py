import os
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# ---------------------------------------------------
# FORCE LOAD .env FROM PROJECT ROOT
# ---------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)

# ---------------------------------------------------
# READ VARIABLES
# ---------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

print("Loaded URL:", SUPABASE_URL)
print("Loaded KEY:", SUPABASE_KEY)

# ---------------------------------------------------
# VALIDATE
# ---------------------------------------------------
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "❌ Supabase credentials not found.\n"
        "Check your .env file contains:\n"
        "SUPABASE_URL=...\n"
        "SUPABASE_KEY=..."
    )

# ---------------------------------------------------
# CREATE CLIENT
# ---------------------------------------------------
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)