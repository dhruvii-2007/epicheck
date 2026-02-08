from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.core.roles import require_admin
from app.supabase_client import supabase

router = APIRouter(prefix="/admin", tags=["Admin"])
@router.get("/users")
def list_users(admin=Depends(require_admin)):
    """
    List all users (profiles)
    """
    resp = (
        supabase
        .table("profiles")
        .select("*")
        .is_("deleted_at", None)
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


@router.put("/users/{user_id}/suspend")
def suspend_user(
    user_id: str,
    payload: dict,
    admin=Depends(require_admin)
):
    """
    Suspend or unsuspend a user
    """
    suspend = payload.get("suspend", True)
    reason = payload.get("reason")

    update_data = {
        "is_suspended": suspend,
        "suspension_reason": reason,
        "suspended_at": datetime.utcnow().isoformat() if suspend else None
    }

    resp = (
        supabase
        .table("profiles")
        .update(update_data)
        .eq("id", user_id)
        .execute()
    )

    if not resp.data:
        raise HTTPException(status_code=404, detail="User not found")

    return {"status": "updated"}


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: str,
    payload: dict,
    admin=Depends(require_admin)
):
    """
    Change user role
    """
    role = payload.get("role")
    allowed_roles = ["user", "doctor", "admin", "support"]

    if role not in allowed_roles:
        raise HTTPException(status_code=400, detail="Invalid role")

    resp = (
        supabase
        .table("profiles")
        .update({
            "role": role,
            "updated_at": datetime.utcnow().isoformat()
        })
        .eq("id", user_id)
        .execute()
    )

    if not resp.data:
        raise HTTPException(status_code=404, detail="User not found")

    return {"status": "role_updated"}
@router.post("/ai-models")
def register_ai_model(
    payload: dict,
    admin=Depends(require_admin)
):
    """
    Register AI model metadata
    """
    required = ["name", "version", "framework"]
    if not all(payload.get(k) for k in required):
        raise HTTPException(status_code=400, detail="Missing required fields")

    resp = supabase.table("ai_models").insert({
        "name": payload["name"],
        "version": payload["version"],
        "framework": payload["framework"],
        "checksum": payload.get("checksum"),
        "trained_at": payload.get("trained_at"),
        "is_active": False
    }).execute()

    return resp.data[0]


@router.put("/ai-models/{model_id}/activate")
def activate_ai_model(
    model_id: str,
    admin=Depends(require_admin)
):
    """
    Activate selected model, deactivate others
    """

    # deactivate all
    supabase.table("ai_models").update({
        "is_active": False
    }).execute()

    # activate target
    resp = (
        supabase
        .table("ai_models")
        .update({
            "is_active": True,
            "deployed_at": datetime.utcnow().isoformat()
        })
        .eq("id", model_id)
        .execute()
    )

    if not resp.data:
        raise HTTPException(status_code=404, detail="Model not found")

    return {"status": "model_activated"}


@router.get("/ai-models")
def list_ai_models(admin=Depends(require_admin)):
    """
    List all AI models
    """
    resp = (
        supabase
        .table("ai_models")
        .select("*")
        .order("deployed_at", desc=True)
        .execute()
    )
    return resp.data or []
@router.get("/feature-flags")
def list_feature_flags(admin=Depends(require_admin)):
    """
    List feature flags
    """
    resp = (
        supabase
        .table("feature_flags")
        .select("*")
        .execute()
    )
    return resp.data or []


@router.put("/feature-flags/{key}")
def update_feature_flag(
    key: str,
    payload: dict,
    admin=Depends(require_admin)
):
    """
    Enable/disable a feature flag
    """
    enabled = payload.get("enabled")

    if enabled is None:
        raise HTTPException(status_code=400, detail="enabled field required")

    resp = (
        supabase
        .table("feature_flags")
        .update({"enabled": enabled})
        .eq("key", key)
        .execute()
    )

    if not resp.data:
        raise HTTPException(status_code=404, detail="Feature flag not found")

    return {"status": "updated"}
