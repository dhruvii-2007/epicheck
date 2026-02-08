from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from app.core.dependencies import get_current_user
from app.supabase_client import supabase
from app.services.audit import log_audit_event

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# --------------------------------------------------
# LIST NOTIFICATIONS
# --------------------------------------------------
@router.get("")
def list_notifications(
    page: int = 1,
    limit: int = 20,
    profile=Depends(get_current_user)
):
    """
    List notifications (unread first)
    """

    if limit > 50:
        limit = 50

    offset = (page - 1) * limit

    resp = (
        supabase
        .table("notifications")
        .select("*", count="exact")
        .eq("user_id", profile["id"])
        .is_("deleted_at", None)
        .order("is_read", desc=False)   # unread first
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return {
        "page": page,
        "limit": limit,
        "total": resp.count,
        "notifications": resp.data or []
    }


# --------------------------------------------------
# MARK AS READ
# --------------------------------------------------
@router.post("/read")
def mark_notifications_read(
    payload: dict,
    profile=Depends(get_current_user)
):
    """
    Mark one or more notifications as read
    """

    notif_ids = payload.get("notification_ids")

    if not notif_ids or not isinstance(notif_ids, list):
        raise HTTPException(
            status_code=400,
            detail="notification_ids must be a list"
        )

    if len(notif_ids) > 100:
        raise HTTPException(
            status_code=400,
            detail="Too many notifications at once"
        )

    supabase.table("notifications").update({
        "is_read": True,
        "updated_at": datetime.utcnow().isoformat()
    }).in_("id", notif_ids) \
     .eq("user_id", profile["id"]) \
     .execute()

    log_audit_event(
        actor_id=profile["id"],
        action="notifications_marked_read",
        target_table="notifications",
        metadata={
            "count": len(notif_ids)
        }
    )

    return {"status": "marked_read"}
