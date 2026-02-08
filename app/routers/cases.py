from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from uuid import uuid4
from datetime import datetime

from app.core.dependencies import get_current_user
from app.supabase_client import supabase
from app.services.notifications import create_notification
from app.services.audit import log_audit_event

router = APIRouter(prefix="/cases", tags=["Cases"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


# --------------------------------------------------
# CREATE CASE
# --------------------------------------------------
@router.post("")
def create_case(payload: dict, profile=Depends(get_current_user)):
    case_data = {
        "user_id": profile["id"],
        "symptoms": payload.get("symptoms"),
        "status": "submitted",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    resp = supabase.table("skin_cases").insert(case_data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create case")

    case = resp.data[0]

    log_audit_event(
        actor_id=profile["id"],
        action="case_created",
        target_table="skin_cases",
        target_id=case["id"],
    )

    create_notification(
        user_id=profile["id"],
        title="Case submitted",
        message="Your skin case has been submitted successfully.",
        notif_type="case_submitted",
        action_url=f"/cases/{case['id']}",
    )

    return case


# --------------------------------------------------
# UPLOAD CASE IMAGE
# --------------------------------------------------
@router.post("/{case_id}/upload")
def upload_case_image(
    case_id: str,
    file: UploadFile = File(...),
    profile=Depends(get_current_user),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid image type")

    case_resp = (
        supabase
        .table("skin_cases")
        .select("id, status")
        .eq("id", case_id)
        .eq("user_id", profile["id"])
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )

    if not case_resp.data:
        raise HTTPException(status_code=404, detail="Case not found")

    if case_resp.data[0]["status"] != "submitted":
        raise HTTPException(status_code=400, detail="Image upload not allowed")

    ext = file.filename.split(".")[-1].lower()
    filename = f"{uuid4()}.{ext}"
    storage_path = f"{case_id}/{filename}"

    upload_resp = supabase.storage.from_("case-images").upload(
        storage_path,
        file.file,
        {"content-type": file.content_type},
    )

    if upload_resp.get("error"):
        raise HTTPException(status_code=500, detail="Image upload failed")

    file_row = (
        supabase
        .table("case_files")
        .insert({
            "case_id": case_id,
            "storage_path": storage_path,
            "created_at": datetime.utcnow().isoformat(),
        })
        .execute()
        .data[0]
    )

    supabase.table("skin_cases").update({
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", case_id).execute()

    log_audit_event(
        actor_id=profile["id"],
        action="case_image_uploaded",
        target_table="case_files",
        target_id=file_row["id"],
        metadata={"filename": filename},
    )

    return {"status": "uploaded"}


# --------------------------------------------------
# ADD SYMPTOMS
# --------------------------------------------------
@router.post("/{case_id}/symptoms")
def add_case_symptoms(case_id: str, payload: dict, profile=Depends(get_current_user)):
    symptoms = payload.get("symptoms")

    if not isinstance(symptoms, list) or not symptoms:
        raise HTTPException(status_code=400, detail="Symptoms must be a non-empty list")

    case_resp = (
        supabase
        .table("skin_cases")
        .select("id, status")
        .eq("id", case_id)
        .eq("user_id", profile["id"])
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )

    if not case_resp.data:
        raise HTTPException(status_code=404, detail="Case not found")

    if case_resp.data[0]["status"] != "submitted":
        raise HTTPException(status_code=400, detail="Cannot modify symptoms")

    rows = [
        {"case_id": case_id, "symptom_code": code}
        for code in set(symptoms)
    ]

    supabase.table("case_symptoms").insert(rows).execute()

    log_audit_event(
        actor_id=profile["id"],
        action="case_symptoms_added",
        target_table="case_symptoms",
        target_id=case_id,
        metadata={"count": len(rows)},
    )

    return {"status": "symptoms_added"}


# --------------------------------------------------
# LIST MY CASES
# --------------------------------------------------
@router.get("")
def list_cases(
    page: int = 1,
    limit: int = 10,
    profile=Depends(get_current_user),
):
    offset = (page - 1) * limit

    resp = (
        supabase
        .table("skin_cases")
        .select(
            "id, status, created_at, ai_primary_label, risk_level, reviewed",
            count="exact",
        )
        .eq("user_id", profile["id"])
        .is_("deleted_at", None)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return {
        "page": page,
        "limit": limit,
        "total": resp.count or 0,
        "cases": resp.data or [],
    }


# --------------------------------------------------
# GET CASE DETAILS (FULL VIEW)
# --------------------------------------------------
@router.get("/{case_id}")
def get_case_details(case_id: str, profile=Depends(get_current_user)):
    case_resp = (
        supabase
        .table("skin_cases")
        .select("*")
        .eq("id", case_id)
        .eq("user_id", profile["id"])
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )

    if not case_resp.data:
        raise HTTPException(status_code=404, detail="Case not found")

    case = case_resp.data[0]

    return {
        "case": case,
        "files": (
            supabase
            .table("case_files")
            .select("id, created_at")
            .eq("case_id", case_id)
            .eq("marked_for_deletion", False)
            .execute()
            .data or []
        ),
        "symptoms": (
            supabase
            .table("case_symptoms")
            .select("*")
            .eq("case_id", case_id)
            .execute()
            .data or []
        ),
        "predictions": (
            supabase
            .table("case_predictions")
            .select("*")
            .eq("case_id", case_id)
            .is_("deleted_at", None)
            .order("created_at", desc=True)
            .execute()
            .data or []
        ),
        "doctor_review": (
            supabase
            .table("doctor_reviews")
            .select(
                "decision, review, created_at, doctor_id, profiles(name, email)"
            )
            .eq("case_id", case_id)
            .limit(1)
            .execute()
            .data or [None]
        )[0],
    }


# --------------------------------------------------
# SOFT DELETE CASE
# --------------------------------------------------
@router.delete("/{case_id}")
def delete_case(case_id: str, profile=Depends(get_current_user)):
    resp = (
        supabase
        .table("skin_cases")
        .update({
            "deleted_at": datetime.utcnow().isoformat()
        })
        .eq("id", case_id)
        .eq("user_id", profile["id"])
        .execute()
    )

    if not resp.data:
        raise HTTPException(status_code=404, detail="Case not found")

    return {"status": "deleted"}
