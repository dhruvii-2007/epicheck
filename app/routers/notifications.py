from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from app.supabase_client import supabase

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# --------------------------------------------------
# LIST NOTIFICATIONS
# --------------------------------------------------
@router.get("")
def list_notifications(profile=Depends(get_current_user)):
    """
    List notifications (unread first)
    """

    resp = (
        supabase
        .table("notifications")
        .select("*")
        .eq("user_id", profile["id"])
        .order("is_read", desc=False)   # unread first
        .order("created_at", desc=True)
        .execute()
    )

    return resp.data or []


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

    supabase.table("notifications").update({
        "is_read": True
    }).in_("id", notif_ids).eq("user_id", profile["id"]).execute()

    return {"status": "marked_read"}
