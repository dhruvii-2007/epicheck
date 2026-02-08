# app/logger.py

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.supabase_client import db_insert

# --------------------------------------------------
# BASE LOGGER CONFIG
# --------------------------------------------------

logger = logging.getLogger("epicheck")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s"
)

handler = RotatingFileHandler(
    filename="epicheck.log",
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=5
)
handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(handler)

# --------------------------------------------------
# AUDIT LOGGING (audit_logs table)
# --------------------------------------------------

def audit_log(
    action: str,
    actor_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
):
    """
    Immutable audit trail.
    """
    try:
        db_insert(
            table="audit_logs",
            payload={
                "actor_id": actor_id,
                "actor_role": actor_role,
                "action": action,
                "details": details,
                "ip_address": ip_address,
                "created_at": datetime.now(timezone.utc),
            }
        )
    except Exception as e:
        # Audit logging must NEVER crash the app
        logger.error(f"AUDIT LOG FAILED: {e}")

# --------------------------------------------------
# REQUEST LOGGING (request_logs table)
# --------------------------------------------------

def request_log(
    user_id: Optional[str],
    ip_address: str,
    endpoint: str,
    method: str,
    status_code: int,
):
    try:
        db_insert(
            table="request_logs",
            payload={
                "user_id": user_id,
                "ip_address": ip_address,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "created_at": datetime.now(timezone.utc),
            }
        )
    except Exception as e:
        logger.error(f"REQUEST LOG FAILED: {e}")
