from datetime import datetime
from app.supabase_client import supabase

JOB_NAME = "system_cron"

def heartbeat():
    supabase.table("cron_health").insert({
        "job_name": JOB_NAME,
        "ran_at": datetime.utcnow().isoformat()
    }).execute()


if __name__ == "__main__":
    heartbeat()
