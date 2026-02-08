from datetime import datetime
from app.supabase_client import supabase

def purge_soft_deleted():
    now = datetime.utcnow().isoformat()

    supabase.table("profiles") \
        .delete() \
        .lt("scheduled_for_deletion_at", now) \
        .execute()

    supabase.table("skin_cases") \
        .delete() \
        .lt("deleted_at", now) \
        .execute()


if __name__ == "__main__":
    purge_soft_deleted()
