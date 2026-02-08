from datetime import datetime
from typing import Optional
from app.supabase_client import supabase


def log_audit_event(
    *,
    actor_id: str,
    action: str,
    target_table: str,
    target_id: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """
    Explicit audit logging for sensitive actions.

    This function MUST be called for:
    - inserts
    - updates
    - deletes
    - role changes
    - status transitions
    """

    # --------------------------------------------------
    # Basic validation (audit logs must be trustworthy)
    # --------------------------------------------------
    if not actor_id:
        return

    if not action or not target_table:
        return

    audit_row = {
        "actor_id": actor_id,
        "action": action,
        "target_table": target_table,
        "target_id": target_id,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat()
    }

    try:
        supabase.table("audit_logs").insert(audit_row).execute()
    except Exception:
        # Audit logging should NEVER block the main action.
        # Failing silently here is intentional.
        pass
