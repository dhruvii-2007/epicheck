# app/supabase_client.py

import os
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from supabase import create_client, Client
from app.logger import logger

# --------------------------------------------------
# INIT
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
# INTERNAL
# --------------------------------------------------

def _apply_soft_delete_filter(query):
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
    include_deleted: bool = False,
):
    try:
        query = supabase.table(table).select("*")

        if not include_deleted:
            query = _apply_soft_delete_filter(query)

        if filters:
            for k, v in filters.items():
                query = query.eq(k, v)

        res = query.single().execute() if single else query.execute()

        if res.error:
            raise RuntimeError(res.error.message)

        return res.data

    except Exception as e:
        logger.exception(f"DB SELECT failed on {table}")
        raise e

# --------------------------------------------------
# INSERT
# --------------------------------------------------

def db_insert(
    table: str,
    payload: Dict[str, Any],
    return_single: bool = True,
):
    try:
        res = supabase.table(table).insert(payload).execute()

        if res.error:
            raise RuntimeError(res.error.message)

        return res.data[0] if return_single else res.data

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
    if not filters:
        raise ValueError("UPDATE requires filters")

    try:
        query = supabase.table(table).update(payload)
        for k, v in filters.items():
            query = query.eq(k, v)

        res = query.execute()

        if res.error:
            raise RuntimeError(res.error.message)

        return res.data

    except Exception as e:
        logger.exception(f"DB UPDATE failed on {table}")
        raise e

# --------------------------------------------------
# SOFT DELETE
# --------------------------------------------------

def db_soft_delete(
    table: str,
    filters: Dict[str, Any],
):
    return db_update(
        table=table,
        filters=filters,
        payload={"deleted_at": datetime.now(timezone.utc)},
    )
