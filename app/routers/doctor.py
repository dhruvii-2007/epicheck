from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from datetime import datetime
from uuid import uuid4
from app.core.dependencies import get_current_user
from app.core.roles import require_doctor, require_admin
from app.supabase_client import supabase

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

    filename = f"{uuid4()}_{file.filename}"
    storage_path = f"doctor-verifications/{profile['id']}/{filename}"

    upload_resp = supabase.storage.from_("documents").upload(
        storage_path,
        file.file,
        {"content-type": file.content_type}
    )

    if upload_resp.get("error"):
        raise HTTPException(status_code=500, detail="Document upload failed")

    document_url = supabase.storage.from_("documents").get_public_url(storage_path)

    supabase.table("doctor_verifications").insert({
        "doctor_id": profile["id"],
        "verification_status": "pending",
        "document_url": document_url,
        "verified_at": datetime.utcnow().isoformat()
    }).execute()

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
        .order("verified_at", desc=True)
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

    # verify doctor exists
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

    # assign
    supabase.table("case_assignments").insert({
        "case_id": case_id,
        "doctor_id": doctor_id,
        "assigned_by": admin["id"],
        "reason": payload.get("reason")
    }).execute()

    supabase.table("skin_cases").update({
        "assigned_doctor": doctor_id,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", case_id).execute()

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

    # verify assignment
    case_resp = (
        supabase
        .table("skin_cases")
        .select("*")
        .eq("id", case_id)
        .eq("assigned_doctor", doctor["id"])
        .execute()
    )

    if not case_resp.data:
        raise HTTPException(status_code=403, detail="Case not assigned to you")

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
        "status": update_status,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", case_id).execute()

    return {"status": "review_submitted"}
create_notification( user_id=doctor_id, title="New case assigned", message="A new skin case has been assigned to you.", notif_type="case_assigned", action_url=f"/cases/{case_id}" )
create_notification( user_id=case["user_id"], title="Case reviewed", message="A doctor has reviewed your case.", notif_type="case_reviewed", action_url=f"/cases/{case_id}" )