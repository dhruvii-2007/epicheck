from supabase import create_client, Client
from app.config import (
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY,
    SUPABASE_ANON_KEY,
)

# --------------------------------------------------
# Service-role client (FULL ACCESS)
# --------------------------------------------------
# ⚠️ Backend only.
# Uses SERVICE ROLE key → bypasses RLS.
# NEVER expose this key to frontend.
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
# Useful if you ever need user-scoped access
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
# Intentionally thin — no business logic here
# --------------------------------------------------

def db_select(table: str, **filters):
    """
    Select rows from a table with equality filters.

    Usage:
        db_select("profiles", id=user_id)
        db_select("cases", status="open")
    """
    query = supabase.table(table).select("*")
    for key, value in filters.items():
        query = query.eq(key, value)
    return query.execute().data


def db_insert(table: str, data: dict):
    """
    Insert a row into a table.

    DB defaults (uuid, timestamps) are respected.
    """
    return supabase.table(table).insert(data).execute().data


def db_update(table: str, data: dict, **filters):
    """
    Update rows in a table.

    ⚠️ Caller MUST provide filters to avoid mass updates.
    """
    query = supabase.table(table).update(data)
    for key, value in filters.items():
        query = query.eq(key, value)
    return query.execute().data
