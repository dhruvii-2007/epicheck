# app/logger.py

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# --------------------------------------------------
# BASE LOGGER
# --------------------------------------------------

logger = logging.getLogger("epicheck")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# --------------------------------------------------
# REQUEST LOGGING (middleware)
# --------------------------------------------------

def request_log(
    user_id: Optional[str],
    ip_address: Optional[str],
    endpoint: str,
    method: str,
    status_code: int,
):
    logger.info(
        f"[REQUEST] user={user_id} ip={ip_address} "
        f"{method} {endpoint} status={status_code}"
    )

# --------------------------------------------------
# AUDIT LOGGING (DB-related)
# --------------------------------------------------

def audit_log(
    action: str,
    entity: str,
    entity_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    logger.info(
        f"[AUDIT] action={action} entity={entity} "
        f"id={entity_id} meta={metadata}"
    )
