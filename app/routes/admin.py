from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from ..auth import require_admin
from ..supabase_client import (
    db_select,
    db_insert,
    db_update
)
from ..config import (
    STATUS_APPROVED,
    STATUS_REJECTED,
    AUDIT_APPROVE_DOCTOR,
    AUDIT_REVOKE_DOCTOR,
    AUDIT_SUSPEND_USER
)

router = APIRouter(
    prefix="/v1/admin",
    tags=["Admin"]
)

# --------------------------------------------------
# APPROVE DOCTOR
# --------------------------------------------------
@router.post("/approve-doctor/{doctor_id}")
def approve_doctor(
    doctor_id: str,
    admin=Depends(require_admin)
):
    profile = db_select(
        table="profiles",
        filters={"id": doctor_id},
        single=True
    )

    if not profile:
        raise HTTPException(status_code=404, detail="Doctor not found")

    db_update(
        table="profiles",
        payload={"status": STATUS_APPROVED},
        filters={"id": doctor_id}
    )

    db_insert(
        table="audit_logs",
        payload={
            "actor_id": admin["sub"],
            "actor_role": "admin",
            "action": AUDIT_APPROVE_DOCTOR,
            "details": {"doctor_id": doctor_id},
            "created_at": datetime.utcnow().isoformat()
        }
    )

    return {"approved": True}


# --------------------------------------------------
# REVOKE / REJECT DOCTOR
# --------------------------------------------------
@router.post("/revoke-doctor/{doctor_id}")
def revoke_doctor(
    doctor_id: str,
    reason: str = Query(..., min_length=3),
    admin=Depends(require_admin)
):
    profile = db_select(
        table="profiles",
        filters={"id": doctor_id},
        single=True
    )

    if not profile:
        raise HTTPException(status_code=404, detail="Doctor not found")

    db_update(
        table="profiles",
        payload={
            "status": STATUS_REJECTED,
            "suspension_reason": reason
        },
        filters={"id": doctor_id}
    )

    db_insert(
        table="audit_logs",
        payload={
            "actor_id": admin["sub"],
            "actor_role": "admin",
            "action": AUDIT_REVOKE_DOCTOR,
            "details": {
                "doctor_id": doctor_id,
                "reason": reason
            },
            "created_at": datetime.utcnow().isoformat()
        }
    )

    return {"revoked": True}


# --------------------------------------------------
# SUSPEND USER
# --------------------------------------------------
@router.post("/suspend-user/{user_id}")
def suspend_user(
    user_id: str,
    reason: str = Query(..., min_length=3),
    admin=Depends(require_admin)
):
    profile = db_select(
        table="profiles",
        filters={"id": user_id},
        single=True
    )

    if not profile:
        raise HTTPException(status_code=404, detail="User not found")

    db_update(
        table="profiles",
        payload={
            "is_suspended": True,
            "suspension_reason": reason,
            "suspended_at": datetime.utcnow().isoformat()
        },
        filters={"id": user_id}
    )

    db_insert(
        table="audit_logs",
        payload={
            "actor_id": admin["sub"],
            "actor_role": "admin",
            "action": AUDIT_SUSPEND_USER,
            "details": {
                "user_id": user_id,
                "reason": reason
            },
            "created_at": datetime.utcnow().isoformat()
        }
    )

    return {"suspended": True}


# --------------------------------------------------
# VIEW AUDIT LOGS
# --------------------------------------------------
@router.get("/audit-logs")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    admin=Depends(require_admin)
):
    logs = (
        db_select("audit_logs")
    )[:limit]

    return {"logs": logs}


# --------------------------------------------------
# VIEW REQUEST LOGS
# --------------------------------------------------
@router.get("/request-logs")
def get_request_logs(
    limit: int = Query(50, ge=1, le=200),
    admin=Depends(require_admin)
):
    logs = (
        db_select("request_logs")
    )[:limit]

    return {"logs": logs}


# --------------------------------------------------
# FEATURE FLAGS
# --------------------------------------------------
@router.get("/feature-flags")
def list_feature_flags(admin=Depends(require_admin)):
    flags = db_select("feature_flags")
    return {"flags": flags}


@router.post("/feature-flags/{key}")
def update_feature_flag(
    key: str,
    enabled: bool,
    admin=Depends(require_admin)
):
    db_update(
        table="feature_flags",
        payload={"enabled": enabled},
        filters={"key": key}
    )

    return {"key": key, "enabled": enabled}
