from datetime import datetime
from app.supabase_client import supabase


def create_notification(
    user_id: str,
    title: str,
    message: str,
    notif_type: str,
    action_url: str | None = None
):
    """
    Create a notification for a user
    """
    supabase.table("notifications").insert({
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": notif_type,
        "action_url": action_url,
        "created_at": datetime.utcnow().isoformat()
    }).execute()
