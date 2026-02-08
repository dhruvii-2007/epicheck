# app/routers/notifications.py

from fastapi import APIRouter, HTTPException
from uuid import UUID
from datetime import datetime, timezone

from app.supabase_client import db_select, db_insert, db_update

router = APIRouter()

# --------------------------------------------------
# GET USER NOTIFICATIONS
# --------------------------------------------------

@router.get("/{user_id}")
def get_notifications(user_id: UUID):
    return db_select(
        table="notifications",
        filters={"user_id": str(user_id)},
    )

# --------------------------------------------------
# MARK NOTIFICATION AS READ
# --------------------------------------------------

@router.patch("/{notification_id}/read")
def mark_as_read(notification_id: UUID):
    updated = db_update(
        table="notifications",
        filters={"id": str(notification_id)},
        payload={"is_read": True}
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Notification not found")

    return updated[0]

# --------------------------------------------------
# CREATE NOTIFICATION (SYSTEM / INTERNAL)
# --------------------------------------------------

@router.post("/")
def create_notification(
    user_id: UUID,
    title: str,
    message: str,
    type: str,
    action_url: str | None = None,
):
    return db_insert(
        table="notifications",
        payload={
            "user_id": str(user_id),
            "title": title,
            "message": message,
            "type": type,
            "action_url": action_url,
            "created_at": datetime.now(timezone.utc),
        }
    )
