from fastapi import APIRouter, Depends, Request, HTTPException
from datetime import datetime, timedelta
from app.core.dependencies import get_current_user
from app.supabase_client import supabase

router = APIRouter(prefix="/me", tags=["Profile"])


@router.get("")
def get_profile(profile=Depends(get_current_user)):
    """
    Fetch own profile
    """
    return profile


@router.put("")
def update_profile(
    payload: dict,
    request: Request,
    profile=Depends(get_current_user)
):
    """
    Update allowed profile fields
    """
    allowed_fields = {"name", "age", "gender", "contact"}
    update_data = {k: v for k, v in payload.items() if k in allowed_fields}

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    update_data["updated_at"] = datetime.utcnow().isoformat()

    supabase.table("profiles").update(update_data).eq(
        "id", profile["id"]
    ).execute()

    # audit log
    supabase.table("audit_logs").insert({
        "actor_id": profile["id"],
        "actor_role": profile["role"],
        "action": "profile_update",
        "details": update_data,
        "ip_address": request.client.host
    }).execute()

    return {"status": "updated"}


@router.delete("")
def delete_profile(
    request: Request,
    profile=Depends(get_current_user)
):
    """
    Soft delete user profile
    """
    deletion_time = datetime.utcnow()
    scheduled_cleanup = deletion_time + timedelta(days=30)

    supabase.table("profiles").update({
        "deleted_at": deletion_time.isoformat(),
        "scheduled_for_deletion_at": scheduled_cleanup.isoformat()
    }).eq("id", profile["id"]).execute()

    # create cleanup job
    supabase.table("system_jobs").insert({
        "job_type": "user_cleanup",
        "related_id": profile["id"],
        "status": "pending"
    }).execute()

    # audit log
    supabase.table("audit_logs").insert({
        "actor_id": profile["id"],
        "actor_role": profile["role"],
        "action": "profile_soft_delete",
        "details": {"scheduled_for_deletion_at": scheduled_cleanup.isoformat()},
        "ip_address": request.client.host
    }).execute()

    return {"status": "scheduled_for_deletion"}
