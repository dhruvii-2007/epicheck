from datetime import datetime
from .supabase_client import db_insert

def log_audit(
    *,
    actor_id: str,
    action: str,
    target_table: str | None = None,
    target_id: str | None = None,
    metadata: dict | None = None
):
    return db_insert(
        "audit_logs",
        {
            "actor_id": actor_id,
            "action": action,
            "target_table": target_table,
            "target_id": target_id,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
    )
