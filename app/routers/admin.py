from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from app.core.roles import require_admin
from app.supabase_client import supabase
from app.services.audit import log_audit_event

router = APIRouter(prefix="/admin", tags=["Admin"])


# --------------------------------------------------
# USERS
# --------------------------------------------------
@router.get("/users")
def list_users(admin=Depends(require_admin)):
    """
    List all active users
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

    # prevent admin self-suspend
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")

    target = (
        supabase
        .table("profiles")
        .select("id, role")
        .eq("id", user_id)
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )

    if not target.data:
        raise HTTPException(status_code=404, detail="User not found")

    if target.data[0]["role"] == "admin":
        raise HTTPException(status_code=403, detail="Cannot suspend another admin")

    update_data = {
        "is_suspended": suspend,
        "suspension_reason": reason,
        "suspended_at": datetime.utcnow().isoformat() if suspend else None,
        "updated_at": datetime.utcnow().isoformat()
    }

    supabase.table("profiles").update(update_data).eq("id", user_id).execute()

    log_audit_event(
        actor_id=admin["id"],
        action="user_suspended" if suspend else "user_unsuspended",
        target_table="profiles",
        target_id=user_id,
        metadata={"reason": reason}
    )

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

    if user_id == admin["id"] and role != "admin":
        raise HTTPException(status_code=400, detail="Cannot change your own role")

    resp = (
        supabase
        .table("profiles")
        .update({
            "role": role,
            "updated_at": datetime.utcnow().isoformat()
        })
        .eq("id", user_id)
        .is_("deleted_at", None)
        .execute()
    )

    if not resp.data:
        raise HTTPException(status_code=404, detail="User not found")

    log_audit_event(
        actor_id=admin["id"],
        action="user_role_updated",
        target_table="profiles",
        target_id=user_id,
        metadata={"role": role}
    )

    return {"status": "role_updated"}


# --------------------------------------------------
# AI MODELS
# --------------------------------------------------
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

    model = resp.data[0]

    log_audit_event(
        actor_id=admin["id"],
        action="ai_model_registered",
        target_table="ai_models",
        target_id=model["id"]
    )

    return model


@router.put("/ai-models/{model_id}/activate")
def activate_ai_model(
    model_id: str,
    admin=Depends(require_admin)
):
    """
    Activate selected model
    """

    model_check = (
        supabase
        .table("ai_models")
        .select("id")
        .eq("id", model_id)
        .limit(1)
        .execute()
    )

    if not model_check.data:
        raise HTTPException(status_code=404, detail="Model not found")

    supabase.table("ai_models").update({"is_active": False}).execute()

    supabase.table("ai_models").update({
        "is_active": True,
        "deployed_at": datetime.utcnow().isoformat()
    }).eq("id", model_id).execute()

    log_audit_event(
        actor_id=admin["id"],
        action="ai_model_activated",
        target_table="ai_models",
        target_id=model_id
    )

    return {"status": "model_activated"}


@router.get("/ai-models")
def list_ai_models(admin=Depends(require_admin)):
    """
    List AI models
    """
    resp = (
        supabase
        .table("ai_models")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


# --------------------------------------------------
# FEATURE FLAGS
# --------------------------------------------------
@router.get("/feature-flags")
def list_feature_flags(admin=Depends(require_admin)):
    resp = supabase.table("feature_flags").select("*").execute()
    return resp.data or []


@router.put("/feature-flags/{key}")
def update_feature_flag(
    key: str,
    payload: dict,
    admin=Depends(require_admin)
):
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

    log_audit_event(
        actor_id=admin["id"],
        action="feature_flag_updated",
        target_table="feature_flags",
        target_id=key,
        metadata={"enabled": enabled}
    )

    return {"status": "updated"}
