from datetime import datetime
from fastapi import HTTPException

from ..supabase_client import (
    db_select,
    db_insert,
    db_update
)
from ..config import (
    NOTIFY_SYSTEM,
    NOTIFY_CASE,
    NOTIFY_ADMIN
)

# --------------------------------------------------
# CREATE NOTIFICATION
# --------------------------------------------------

def create_notification(
    *,
    user_id: str,
    title: str,
    message: str,
    type: str = NOTIFY_SYSTEM,
    action_url: str | None = None
):
    """
    Creates a notification for a user.
    """

    return db_insert(
        table="notifications",
        payload={
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": type,
            "action_url": action_url,
            "is_read": False,
            "created_at": datetime.utcnow().isoformat()
        }
    )


# --------------------------------------------------
# GET USER NOTIFICATIONS
# --------------------------------------------------

def get_user_notifications(user_id: str):
    """
    Fetch all notifications for a user.
    """

    return db_select(
        table="notifications",
        filters={
            "user_id": user_id
        }
    )


# --------------------------------------------------
# MARK NOTIFICATION AS READ
# --------------------------------------------------

def mark_notification_read(notification_id: str, user_id: str):
    """
    Marks a notification as read.
    """

    notification = db_select(
        table="notifications",
        filters={"id": notification_id},
        single=True
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    db_update(
        table="notifications",
        payload={"is_read": True},
        filters={"id": notification_id}
    )

    return {"read": True}


# --------------------------------------------------
# ADMIN BROADCAST (SYSTEM)
# --------------------------------------------------

def broadcast_system_notification(
    *,
    user_ids: list[str],
    title: str,
    message: str,
    action_url: str | None = None
):
    """
    Broadcasts a system notification to multiple users.
    """

    created = []

    for uid in user_ids:
        created.append(
            create_notification(
                user_id=uid,
                title=title,
                message=message,
                type=NOTIFY_ADMIN,
                action_url=action_url
            )
        )

    return created


# --------------------------------------------------
# REALTIME HOOK (SUPABASE CHANNEL)
# --------------------------------------------------
# NOTE:
# Supabase Realtime listens automatically to INSERTs on
# notifications table. Frontend subscribes to:
# channel: "notifications:user_id"
#
# No backend websocket required.
# --------------------------------------------------
