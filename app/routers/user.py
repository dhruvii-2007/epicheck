from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from datetime import datetime

from ..auth import require_user
from ..supabase_client import db_select, db_insert, db_update
from ..validators import validate_image
from ..inference import predict_image
from ..config import (
    CASE_SUBMITTED,
    AUDIT_AI_PREDICTION
)

router = APIRouter(tags=["User"])

# --------------------------------------------------
# CREATE SKIN CASE (AI + IMAGE)
# --------------------------------------------------
@router.post("/user/cases")
async def create_case(
    file: UploadFile = File(...),
    symptoms: str | None = None,
    user=Depends(require_user)
):
    contents = await file.read()
    validate_image(file, len(contents))

    # TODO: replace with real storage (Supabase Storage / S3)
    image_url = f"uploads/{user['sub']}/{datetime.utcnow().timestamp()}.jpg"

    # AI inference (stub)
    label, confidence = predict_stub()

    case = db_insert(
        table="skin_cases",
        payload={
            "user_id": user["sub"],
            "image_url": image_url,
            "symptoms": symptoms,
            "ai_primary_label": label,
            "ai_confidence": confidence,
            "status": CASE_SUBMITTED,
            "created_at": datetime.utcnow().isoformat()
        }
    )

    db_insert(
        table="audit_logs",
        payload={
            "actor_id": user["sub"],
            "actor_role": "user",
            "action": AUDIT_AI_PREDICTION,
            "target_table": "skin_cases",
            "target_id": case["id"],
            "details": {
                "label": label,
                "confidence": confidence
            },
            "created_at": datetime.utcnow().isoformat()
        }
    )

    return {
        "case_id": case["id"],
        "ai_label": label,
        "confidence": confidence
    }


# --------------------------------------------------
# GET MY CASES
# --------------------------------------------------
@router.get("/user/cases")
def get_my_cases(user=Depends(require_user)):
    cases = db_select(
        table="skin_cases",
        filters={
            "user_id": user["sub"],
            "deleted_at": None
        }
    )
    return {"cases": cases}


# --------------------------------------------------
# GET SINGLE CASE
# --------------------------------------------------
@router.get("/user/cases/{case_id}")
def get_case(case_id: str, user=Depends(require_user)):
    case = db_select(
        table="skin_cases",
        filters={"id": case_id},
        single=True
    )

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case["user_id"] != user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")

    predictions = db_select(
        table="case_predictions",
        filters={"case_id": case_id}
    )

    reviews = db_select(
        table="doctor_reviews",
        filters={"case_id": case_id}
    )

    return {
        "case": case,
        "predictions": predictions,
        "reviews": reviews
    }


# --------------------------------------------------
# DELETE (SOFT) CASE
# --------------------------------------------------
@router.delete("/user/cases/{case_id}")
def delete_case(case_id: str, user=Depends(require_user)):
    case = db_select(
        table="skin_cases",
        filters={"id": case_id},
        single=True
    )

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case["user_id"] != user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    db_update(
        table="skin_cases",
        payload={"deleted_at": datetime.utcnow().isoformat()},
        filters={"id": case_id}
    )

    return {"deleted": True}


# --------------------------------------------------
# USER CONSENT
# --------------------------------------------------
@router.post("/user/consent")
def give_consent(
    consent_type: str,
    consent_version: str,
    user=Depends(require_user)
):
    db_insert(
        table="user_consents",
        payload={
            "user_id": user["sub"],
            "consent_type": consent_type,
            "consent_version": consent_version,
            "accepted_at": datetime.utcnow().isoformat()
        }
    )
    return {"consent_saved": True}
