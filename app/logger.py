import logging
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from app.supabase_client import db_insert

# --------------------------------------------------
# BASE LOGGER CONFIG
# --------------------------------------------------

logger = logging.getLogger("epicheck")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] %(message)s"
)
handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(handler)

# --------------------------------------------------
# AUDIT LOG (USED BY ROUTERS)
# --------------------------------------------------

def audit_log(
    *,
    action: str,
    entity: str,
    entity_id: Optional[str] = None,
    performed_by: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Writes an audit event to Supabase.
    This function MUST exist — routers depend on it.
    """

    payload = {
        "action": action,
        "entity": entity,
        "entity_id": entity_id,
        "performed_by": performed_by,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        db_insert("audit_logs", payload)
        logger.info(
            f"AUDIT | {action} | {entity} | id={entity_id} | by={performed_by}"
        )
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}", exc_info=True)
