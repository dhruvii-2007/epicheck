from datetime import datetime
from app.supabase_client import supabase

def log_audit_event(
    *,
    actor_id: str,
    action: str,
    target_table: str,
    target_id: str | None = None,
    metadata: dict | None = None
):
    """
    Explicit audit logging for sensitive actions
    """
    supabase.table("audit_logs").insert({
        "actor_id": actor_id,
        "action": action,
        "target_table": target_table,
        "target_id": target_id,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat()
    }).execute()
