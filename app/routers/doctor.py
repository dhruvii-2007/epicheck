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
# DOCTOR VERIFICATION
# --------------------------------------------------
@router.post("/doctor/verify")
def submit_verification(
    file: UploadFile = File(...),
    profile=Depends(get_current_user)
):
    """
    Doctor submits verification document
    """

    if profile["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can verify")

    # prevent duplicate pending verification
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

    upload_resp = supabase.storage.from_("documents").upload(
        storage_path,
        file.file,
        {"content-type": file.content_type}
    )

    if upload_resp.get("error"):
        raise HTTPException(status_code=500, detail="Document upload failed")

    supabase.table("doctor_verifications").insert({
        "doctor_id": profile["id"],
        "verification_status": "pending",
        "document_path": storage_path,
        "submitted_at": datetime.utcnow().isoformat()
    }).execute()

    # notify admins
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


@router.get("/doctor/verify/status")
def verification_status(profile=Depends(get_current_user)):
    """
    Get doctor verification status
    """

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
# CASE ASSIGNMENT (ADMIN)
# --------------------------------------------------
@router.post("/cases/{case_id}/assign")
def assign_case(
    case_id: str,
    payload: dict,
    admin=Depends(require_admin)
):
    """
    Assign case to a doctor
    """

    doctor_id = payload.get("doctor_id")
    if not doctor_id:
        raise HTTPException(status_code=400, detail="doctor_id required")

    # verify case exists and open
    case_resp = (
        supabase
        .table("skin_cases")
        .select("id, status")
        .eq("id", case_id)
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )

    if not case_resp.data:
        raise HTTPException(status_code=404, detail="Case not found")

    if case_resp.data[0]["status"] in ["closed"]:
        raise HTTPException(status_code=400, detail="Case already closed")

    # verify doctor
    doc_resp = (
        supabase
        .table("profiles")
        .select("id")
        .eq("id", doctor_id)
        .eq("role", "doctor")
        .eq("status", "approved")
        .execute()
    )

    if not doc_resp.data:
        raise HTTPException(status_code=404, detail="Doctor not found or not approved")

    # atomic assignment
    assign_resp = (
        supabase
        .table("case_assignments")
        .insert({
            "case_id": case_id,
            "doctor_id": doctor_id,
            "assigned_by": admin["id"],
            "reason": payload.get("reason"),
            "created_at": datetime.utcnow().isoformat()
        })
        .execute()
    )

    if not assign_resp.data:
        raise HTTPException(status_code=409, detail="Case already assigned")

    supabase.table("skin_cases").update({
        "assigned_doctor": doctor_id,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", case_id).execute()

    create_notification(
        user_id=doctor_id,
        title="New case assigned",
        message="A new skin case has been assigned to you.",
        notif_type="case_assigned",
        action_url=f"/cases/{case_id}"
    )

    log_audit_event(
        actor_id=admin["id"],
        action="case_assigned",
        target_table="skin_cases",
        target_id=case_id,
        metadata={"doctor_id": doctor_id}
    )

    return {"status": "assigned"}


# --------------------------------------------------
# DOCTOR REVIEW
# --------------------------------------------------
@router.post("/cases/{case_id}/review")
def review_case(
    case_id: str,
    payload: dict,
    doctor=Depends(require_doctor)
):
    """
    Doctor reviews AI result
    """

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

    if case["status"] not in ["reviewed"]:
        raise HTTPException(status_code=400, detail="Case not ready for review")

    # prevent duplicate review
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

    update_status = "closed" if decision in ["approved", "rejected"] else "reviewed"

    supabase.table("skin_cases").update({
        "reviewed": True,
        "reviewed_at": datetime.utcnow().isoformat(),
        "reviewed_by": doctor["id"],
        "status": update_status,
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
