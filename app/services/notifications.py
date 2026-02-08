from datetime import datetime
from app.supabase_client import supabase


ALLOWED_NOTIFICATION_TYPES = {
    "case_submitted",
    "case_assigned",
    "case_reviewed",
    "ticket_reply",
    "system"
}


def create_notification(
    *,
    user_id: str,
    title: str,
    message: str,
    notif_type: str,
    action_url: str | None = None
) -> None:
    """
    Create a notification for a user.

    Rules:
    - User must exist and not be soft-deleted
    - Notification type must be valid
    - Notifications are unread by default
    """

    if not user_id:
        return

    if not title or not message:
        return

    if notif_type not in ALLOWED_NOTIFICATION_TYPES:
        raise ValueError(f"Invalid notification type: {notif_type}")

    # Ensure user exists and is active
    profile_check = (
        supabase
        .table("profiles")
        .select("id")
        .eq("id", user_id)
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )

    if not profile_check.data:
        # Never notify deleted / missing users
        return

    from app.supabase_client import db_insert

