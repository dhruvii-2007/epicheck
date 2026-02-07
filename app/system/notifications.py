from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from app.supabase_client import (
    db_select,
    db_insert,
    db_update
)
from app.config import (
    NOTIFY_SYSTEM,
    NOTIFY_CASE,
    NOTIFY_ADMIN
)
from app.auth import require_user, require_admin

router = APIRouter()

# --------------------------------------------------
# INTERNAL HELPERS
# --------------------------------------------------

def create_notification(
    *,
    user_id: str,
    title: str,
    message: str,
    type: str = NOTIFY_SYSTEM,
    action_url: str | None = None
):
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
# USER: GET MY NOTIFICATIONS
# --------------------------------------------------
@router.get("/")
def get_my_notifications(user=Depends(require_user)):
    return db_select(
        table="notifications",
        filters={"user_id": user["id"]},
        order="created_at.desc"
    )


# --------------------------------------------------
# USER: MARK AS READ
# --------------------------------------------------
@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    user=Depends(require_user)
):
    notification = db_select(
        table="notifications",
        filters={"id": notification_id},
        single=True
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    db_update(
        table="notifications",
        payload={"is_read": True},
        filters={"id": notification_id}
    )

    return {"read": True}


# --------------------------------------------------
# ADMIN: BROADCAST SYSTEM NOTIFICATION
# --------------------------------------------------
@router.post("/broadcast")
def broadcast_system_notification(
    payload: dict,
    admin=Depends(require_admin)
):
    """
    payload = {
        "user_ids": [...],
        "title": "...",
        "message": "...",
        "action_url": "optional"
    }
    """

    created = []

    for uid in payload["user_ids"]:
        created.append(
            create_notification(
                user_id=uid,
                title=payload["title"],
                message=payload["message"],
                type=NOTIFY_ADMIN,
                action_url=payload.get("action_url")
            )
        )

    return {
        "sent": len(created)
    }


# --------------------------------------------------
# REALTIME NOTES
# --------------------------------------------------
# Supabase Realtime listens automatically to INSERTs on
# notifications table.
#
# Frontend subscribes to:
# channel: "notifications:user_id"
#
# No backend websocket needed.
# --------------------------------------------------
