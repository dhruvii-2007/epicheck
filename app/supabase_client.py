from supabase import create_client, Client
from app.config import (
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY,
    SUPABASE_ANON_KEY,
)

# --------------------------------------------------
# Service-role client (FULL ACCESS)
# ⚠️ Backend only. Never expose this key to frontend.
# Bypasses RLS — use carefully and intentionally.
# --------------------------------------------------

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("Supabase service configuration is missing")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)

# --------------------------------------------------
# Optional anon client (RLS enforced)
# --------------------------------------------------

supabase_anon: Client | None = None

if SUPABASE_ANON_KEY:
    supabase_anon = create_client(
        SUPABASE_URL,
        SUPABASE_ANON_KEY
    )
