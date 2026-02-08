# app/logger.py

import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.supabase_client import supabase

# --------------------------------------------------
# PYTHON LOGGER (stdout / Render)
# --------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("epicheck")

# --------------------------------------------------
# REQUEST LOGGING (request_logs table)
# --------------------------------------------------

def request_log(
    *,
    user_id: Optional[str],
    ip_address: Optional[str],
    endpoint: str,
    method: str,
    status_code: int,
):
    """
    Logs every API request.
    Matches `request_logs` table exactly.
    """
    try:
        supabase.table("request_logs").insert({
            "user_id": user_id,
            "ip_address": ip_address,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "created_at": datetime.now(timezone.utc),
        }).execute()

    except Exception as e:
        # Never break API due to logging failure
        logger.warning(f"Request log failed: {e}")

# --------------------------------------------------
# AUDIT LOGGING (audit_logs table)
# --------------------------------------------------

def audit_log(
    *,
    table_name: str,
    record_id: str,
    action: str,
    actor_id: Optional[str],
    old_data: Optional[Dict[str, Any]] = None,
    new_data: Optional[Dict[str, Any]] = None,
):
    """
    Application-level audit logs.
    Complements DB triggers.
    """
    try:
        supabase.table("audit_logs").insert({
            "table_name": table_name,
            "record_id": record_id,
            "action": action,
            "actor_id": actor_id,
            "old_data": old_data,
            "new_data": new_data,
            "created_at": datetime.now(timezone.utc),
        }).execute()

    except Exception as e:
        logger.warning(f"Audit log failed: {e}")
