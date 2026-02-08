# app/supabase_client.py

import os
from typing import Any, Dict, List, Optional
from supabase import create_client, Client
from app.logger import logger

# --------------------------------------------------
# SUPABASE CLIENT INIT
# --------------------------------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    raise RuntimeError("Supabase credentials are not set")

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)

# --------------------------------------------------
# INTERNAL HELPERS
# --------------------------------------------------

def _apply_soft_delete_filter(query):
    """
    Enforces deleted_at IS NULL if column exists.
    Safe to call on all tables.
    """
    try:
        return query.is_("deleted_at", "null")
    except Exception:
        return query

# --------------------------------------------------
# SELECT
# --------------------------------------------------

def db_select(
    table: str,
    filters: Optional[Dict[str, Any]] = None,
    single: bool = False,
    include_deleted: bool = False
):
    """
    Generic SELECT wrapper.
    """
    try:
        query = supabase.table(table).select("*")

        if not include_deleted:
            query = _apply_soft_delete_filter(query)

        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        response = query.single().execute() if single else query.execute()

        if response.error:
            raise RuntimeError(response.error.message)

        return response.data

    except Exception as e:
        logger.exception(f"DB SELECT failed on {table}")
        raise e

# --------------------------------------------------
# INSERT
# --------------------------------------------------

def db_insert(
    table: str,
    payload: Dict[str, Any],
    return_single: bool = True
):
    """
    INSERT with RETURNING *
    """
    try:
        response = (
            supabase
            .table(table)
            .insert(payload)
            .execute()
        )

        if response.error:
            raise RuntimeError(response.error.message)

        if return_single:
            return response.data[0]

        return response.data

    except Exception as e:
        logger.exception(f"DB INSERT failed on {table}")
        raise e

# --------------------------------------------------
# UPDATE
# --------------------------------------------------

def db_update(
    table: str,
    filters: Dict[str, Any],
    payload: Dict[str, Any],
):
    """
    UPDATE with strict filters.
    """
    if not filters:
        raise ValueError("UPDATE requires filters")

    try:
        query = supabase.table(table).update(payload)

        for key, value in filters.items():
            query = query.eq(key, value)

        response = query.execute()

        if response.error:
            raise RuntimeError(response.error.message)

        return response.data

    except Exception as e:
        logger.exception(f"DB UPDATE failed on {table}")
        raise e

# --------------------------------------------------
# SOFT DELETE
# --------------------------------------------------

def db_soft_delete(
    table: str,
    filters: Dict[str, Any]
):
    """
    Sets deleted_at = now()
    """
    from datetime import datetime, timezone

    return db_update(
        table=table,
        filters=filters,
        payload={"deleted_at": datetime.now(timezone.utc)}
    )
