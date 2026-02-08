from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from uuid import uuid4
from datetime import datetime
from app.core.dependencies import get_current_user
from app.supabase_client import supabase

router = APIRouter(prefix="/cases", tags=["Cases"])


# --------------------------------------------------
# CREATE CASE
# --------------------------------------------------
@router.post("")
def create_case(
    payload: dict,
    profile=Depends(get_current_user)
):
    """
    Create a new skin case
    """
    case_data = {
        "user_id": profile["id"],
        "symptoms": payload.get("symptoms"),
        "status": "submitted",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    resp = supabase.table("skin_cases").insert(case_data).execute()

    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create case")

    return resp.data[0]


# --------------------------------------------------
# UPLOAD CASE IMAGE
# --------------------------------------------------
@router.post("/{case_id}/upload")
def upload_case_image(
    case_id: str,
    file: UploadFile = File(...),
    profile=Depends(get_current_user)
):
    """
    Upload case image to Supabase storage
    """

    # verify ownership
    case_resp = (
        supabase
        .table("skin_cases")
        .select("id")
        .eq("id", case_id)
        .eq("user_id", profile["id"])
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )

    if not case_resp.data:
        raise HTTPException(status_code=404, detail="Case not found")

    # validate path
    filename = f"{uuid4()}.{file.filename.split('.')[-1]}"
    storage_path = f"case-images/{case_id}/{filename}"

    # upload to storage
    upload_resp = supabase.storage.from_("case-images").upload(
        storage_path,
        file.file,
        {"content-type": file.content_type}
    )

    if upload_resp.get("error"):
        raise HTTPException(status_code=500, detail="Image upload failed")

    public_url = supabase.storage.from_("case-images").get_public_url(storage_path)

    # insert into case_files
    supabase.table("case_files").insert({
        "case_id": case_id,
        "file_url": public_url
    }).execute()

    # update skin_cases
    supabase.table("skin_cases").update({
        "image_url": public_url,
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", case_id).execute()

    return {
        "status": "uploaded",
        "image_url": public_url
    }


# --------------------------------------------------
# ADD SYMPTOMS
# --------------------------------------------------
@router.post("/{case_id}/symptoms")
def add_case_symptoms(
    payload: dict,
    case_id: str,
    profile=Depends(get_current_user)
):
    """
    Add structured symptoms to a case
    """
    symptoms = payload.get("symptoms")

    if not isinstance(symptoms, list):
        raise HTTPException(status_code=400, detail="Symptoms must be a list")

    # verify ownership
    case_resp = (
        supabase
        .table("skin_cases")
        .select("id")
        .eq("id", case_id)
        .eq("user_id", profile["id"])
        .is_("deleted_at", None)
        .execute()
    )

    if not case_resp.data:
        raise HTTPException(status_code=404, detail="Case not found")

    rows = [
        {
            "case_id": case_id,
            "symptom_code": s
        }
        for s in symptoms
    ]

    supabase.table("case_symptoms").insert(rows).execute()

    return {"status": "symptoms_added"}


# --------------------------------------------------
# LIST USER CASES
# --------------------------------------------------
@router.get("")
def list_cases(
    page: int = 1,
    limit: int = 10,
    profile=Depends(get_current_user)
):
    """
    Paginated list of user's cases
    """
    offset = (page - 1) * limit

    resp = (
        supabase
        .table("skin_cases")
        .select("*")
        .eq("user_id", profile["id"])
        .is_("deleted_at", None)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return {
        "page": page,
        "limit": limit,
        "cases": resp.data or []
    }


# --------------------------------------------------
# GET CASE DETAILS
# --------------------------------------------------
@router.get("/{case_id}")
def get_case_details(
    case_id: str,
    profile=Depends(get_current_user)
):
    """
    Get full case details
    """

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

    predictions = (
        supabase
        .table("case_predictions")
        .select("*")
        .eq("case_id", case_id)
        .is_("deleted_at", None)
        .execute()
    ).data or []

    reviews = (
        supabase
        .table("doctor_reviews")
        .select("*")
        .eq("case_id", case_id)
        .is_("deleted_at", None)
        .execute()
    ).data or []

    files = (
        supabase
        .table("case_files")
        .select("*")
        .eq("case_id", case_id)
        .eq("marked_for_deletion", False)
        .execute()
    ).data or []

    symptoms = (
        supabase
        .table("case_symptoms")
        .select("*")
        .eq("case_id", case_id)
        .execute()
    ).data or []

    return {
        "case": case,
        "files": files,
        "symptoms": symptoms,
        "predictions": predictions,
        "doctor_reviews": reviews
    }
from app.services.notifications import create_notification

create_notification(
    user_id=profile["id"],
    title="Case submitted",
    message="Your skin case has been submitted successfully.",
    notif_type="case_submitted",
    action_url=f"/cases/{case_id}"
)
