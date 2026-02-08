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
# --------------------------------------------------
# Lightweight DB helper wrappers
# --------------------------------------------------

def db_select(table: str, **filters):
    query = supabase.table(table).select("*")
    for key, value in filters.items():
        query = query.eq(key, value)
    return query.execute().data


def db_insert(table: str, data: dict):
    return supabase.table(table).insert(data).execute().data


def db_update(table: str, data: dict, **filters):
    query = supabase.table(table).update(data)
    for key, value in filters.items():
        query = query.eq(key, value)
    return query.execute().data
