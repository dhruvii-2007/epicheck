from datetime import datetime, timedelta
from app.supabase_client import supabase

REQUEST_LOG_RETENTION_DAYS = 30
AUDIT_LOG_RETENTION_DAYS = 180

def cleanup_old_logs():
    now = datetime.utcnow()

    request_cutoff = (now - timedelta(days=REQUEST_LOG_RETENTION_DAYS)).isoformat()
    audit_cutoff = (now - timedelta(days=AUDIT_LOG_RETENTION_DAYS)).isoformat()

    supabase.table("request_logs") \
        .delete() \
        .lt("created_at", request_cutoff) \
        .execute()

    supabase.table("audit_logs") \
        .delete() \
        .lt("created_at", audit_cutoff) \
        .execute()
