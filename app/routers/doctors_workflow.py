from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from datetime import datetime
from uuid import uuid4

from app.core.dependencies import get_current_user
from app.core.roles import require_doctor, require_admin
from app.supabase_client import supabase
from app.services.notifications import create_notification
from app.services.audit import log_audit_event

router = APIRouter(tags=["Doctor Workflow"])


# --------------------------------------------------
# DOCTOR VERIFICATION (SUBMIT)
# --------------------------------------------------
@router.post("/doctor/verify")
def submit_verification(
    file: UploadFile = File(...),
    profile=Depends(get_current_user)
):
    if profile["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can verify")

    existing = (
        supabase
        .table("doctor_verifications")
        .select("id")
        .eq("doctor_id", profile["id"])
        .eq("verification_status", "pending")
        .execute()
    )

    if existing.data:
        raise HTTPException(status_code=400, detail="Verification already pending")

    filename = f"{uuid4()}_{file.filename}"
    storage_path = f"doctor-verifications/{profile['id']}/{filename}"

    upload = supabase.storage.from_("documents").upload(
        storage_path,
        file.file,
        {"content-type": file.content_type}
    )

    if upload.get("error"):
        raise HTTPException(status_code=500, detail="Upload failed")

    supabase.table("doctor_verifications").insert({
        "doctor_id": profile["id"],
        "verification_status": "pending",
        "document_path": storage_path,
        "submitted_at": datetime.utcnow().isoformat()
    }).execute()

    admins = (
        supabase
        .table("profiles")
        .select("id")
        .eq("role", "admin")
        .execute()
    )

    for admin in admins.data or []:
        create_notification(
            user_id=admin["id"],
            title="Doctor verification pending",
            message="A doctor has submitted verification documents.",
            notif_type="system",
            action_url="/admin/doctors"
        )

    log_audit_event(
        actor_id=profile["id"],
        action="doctor_verification_submitted",
        target_table="doctor_verifications",
        target_id=profile["id"]
    )

    return {"status": "verification_submitted"}


# --------------------------------------------------
# DOCTOR VERIFICATION STATUS
# --------------------------------------------------
@router.get("/doctor/verify/status")
def verification_status(profile=Depends(get_current_user)):
    resp = (
        supabase
        .table("doctor_verifications")
        .select("*")
        .eq("doctor_id", profile["id"])
        .order("submitted_at", desc=True)
        .limit(1)
        .execute()
    )

    return resp.data[0] if resp.data else {"status": "not_submitted"}


# --------------------------------------------------
# CLAIM NEXT AVAILABLE CASE (AUTO ASSIGN)
# --------------------------------------------------
@router.post("/doctor/cases/next")
def claim_next_case(doctor=Depends(require_doctor)):
    case_resp = (
        supabase
        .table("skin_cases")
        .select("id")
        .eq("status", "reviewed")
        .is_("assigned_doctor", None)
        .is_("deleted_at", None)
        .order("created_at")
        .limit(1)
        .execute()
    )

    if not case_resp.data:
        return {"status": "no_cases_available"}

    case_id = case_resp.data[0]["id"]

    claim = (
        supabase
        .table("skin_cases")
        .update({
            "assigned_doctor": doctor["id"],
            "updated_at": datetime.utcnow().isoformat()
        })
        .eq("id", case_id)
        .is_("assigned_doctor", None)
        .execute()
    )

    if not claim.data:
        raise HTTPException(
            status_code=409,
            detail="Case already claimed"
        )

    log_audit_event(
        actor_id=doctor["id"],
        action="case_claimed",
        target_table="skin_cases",
        target_id=case_id
    )

    return {
        "status": "claimed",
        "case_id": case_id
    }


# --------------------------------------------------
# LIST DOCTOR'S ACTIVE CASES
# --------------------------------------------------
@router.get("/doctor/cases")
def list_my_cases(doctor=Depends(require_doctor)):
    resp = (
        supabase
        .table("skin_cases")
        .select(
            "id, status, created_at, ai_primary_label, risk_level"
        )
        .eq("assigned_doctor", doctor["id"])
        .is_("deleted_at", None)
        .order("created_at", desc=True)
        .execute()
    )

    return resp.data or []


# --------------------------------------------------
# REVIEW CASE
# --------------------------------------------------
@router.post("/cases/{case_id}/review")
def review_case(
    case_id: str,
    payload: dict,
    doctor=Depends(require_doctor)
):
    decision = payload.get("decision")
    review_text = payload.get("review")

    if decision not in ["approved", "rejected", "needs_more_info"]:
        raise HTTPException(status_code=400, detail="Invalid decision")

    case_resp = (
        supabase
        .table("skin_cases")
        .select("*")
        .eq("id", case_id)
        .eq("assigned_doctor", doctor["id"])
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )

    if not case_resp.data:
        raise HTTPException(status_code=403, detail="Case not assigned to you")

    case = case_resp.data[0]

    if case["status"] != "reviewed":
        raise HTTPException(status_code=400, detail="Case not ready for review")

    existing = (
        supabase
        .table("doctor_reviews")
        .select("id")
        .eq("case_id", case_id)
        .eq("doctor_id", doctor["id"])
        .execute()
    )

    if existing.data:
        raise HTTPException(status_code=400, detail="Case already reviewed")

    supabase.table("doctor_reviews").insert({
        "case_id": case_id,
        "doctor_id": doctor["id"],
        "review": review_text,
        "decision": decision,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    new_status = "closed" if decision in ["approved", "rejected"] else "reviewed"

    supabase.table("skin_cases").update({
        "reviewed": True,
        "reviewed_at": datetime.utcnow().isoformat(),
        "reviewed_by": doctor["id"],
        "status": new_status,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", case_id).execute()

    create_notification(
        user_id=case["user_id"],
        title="Case reviewed",
        message="A doctor has reviewed your case.",
        notif_type="case_reviewed",
        action_url=f"/cases/{case_id}"
    )

    log_audit_event(
        actor_id=doctor["id"],
        action="case_reviewed",
        target_table="skin_cases",
        target_id=case_id,
        metadata={"decision": decision}
    )

    return {"status": "review_submitted"}
