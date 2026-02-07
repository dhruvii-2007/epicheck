import os
from dotenv import load_dotenv
from supabase import create_client
from fastapi import HTTPException

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("Supabase environment variables not set")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)

# --------------------------------------------------
# GENERIC HELPERS
# --------------------------------------------------

def db_select(
    table: str,
    filters: dict | None = None,
    single: bool = False
):
    try:
        query = supabase.table(table).select("*")

        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        result = query.execute().data

        if single:
            return result[0] if result else None

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"DB select failed on {table}: {e}"
        )


def db_insert(
    table: str,
    payload: dict
):
    try:
        return (
            supabase
            .table(table)
            .insert(payload)
            .execute()
            .data[0]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"DB insert failed on {table}: {e}"
        )


def db_update(
    table: str,
    payload: dict,
    filters: dict
):
    try:
        query = supabase.table(table).update(payload)

        for key, value in filters.items():
            query = query.eq(key, value)

        return query.execute().data

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"DB update failed on {table}: {e}"
        )


def db_soft_delete(
    table: str,
    filters: dict
):
    try:
        query = supabase.table(table).update({"deleted_at": "now()"})

        for key, value in filters.items():
            query = query.eq(key, value)

        return query.execute().data

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"DB delete failed on {table}: {e}"
        )
