import os
from typing import List

# --------------------------------------------------
# Environment
# --------------------------------------------------

ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
DEBUG = ENVIRONMENT != "production"

# --------------------------------------------------
# Supabase
# --------------------------------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("Missing required Supabase environment variables")

# --------------------------------------------------
# Frontend / CORS
# --------------------------------------------------

FRONTEND_ORIGINS: List[str] = os.getenv(
    "FRONTEND_ORIGINS",
    "http://epicheck.great-site.net",
        "https://epicheck.great-site.net"
).split(",")

# --------------------------------------------------
# AI / System Flags
# --------------------------------------------------

AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"
AI_TIMEOUT_SECONDS = int(os.getenv("AI_TIMEOUT_SECONDS", "30"))

# --------------------------------------------------
# Logging
# --------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
