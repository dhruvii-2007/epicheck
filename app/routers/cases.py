from fastapi import APIRouter, HTTPException
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from app.supabase_client import (
    db_select,
    db_insert,
    db_update,
)
from app.config import (
    CASE_SUBMITTED,
    CASE_PROCESSING,
    CASE_REVIEWED,
    CASE_CLOSED,
    VALID_CASE_STATUSES,
)
from app.logger import audit_log

router = APIRouter()

# --------------------------------------------------
# CREATE CASE
# --------------------------------------------------

@router.post("/")
def create_case(
    user_id: UUID,
    image_url: str,
    symptom_codes: Optional[List[str]] = None,
    symptoms_text: Optional[str] = None,
):
    case = db_insert(
        table="skin_cases",
        payload={
            "user_id": str(user_id),
            "image_url": image_url,
            "symptoms": symptoms_text,
            "status": CASE_SUBMITTED,
            "created_at": datetime.now(timezone.utc),
        }
    )

    if symptom_codes:
        for code in symptom_codes:
            db_insert(
                table="case_symptoms",
                payload={
                    "case_id": case["id"],
                    "symptom_code": code,
                }
            )

    audit_log(
        action="case_created",
        actor_id=str(user_id),
        actor_role="user",
        details={"case_id": case["id"]},
    )

    return case

# --------------------------------------------------
# GET CASE (FULL VIEW)
# --------------------------------------------------

@router.get("/{case_id}")
def get_case(case_id: UUID):
    case = db_select(
        table="skin_cases",
        filters={"id": str(case_id)},
        single=True
    )

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case["predictions"] = db_select(
        table="case_predictions",
        filters={"case_id": str(case_id)},
    )

    case["files"] = db_select(
        table="case_files",
        filters={"case_id": str(case_id)},
    )

    case["symptoms_structured"] = db_select(
        table="case_symptoms",
        filters={"case_id": str(case_id)},
    )

    return case

# --------------------------------------------------
# UPDATE CASE STATUS
# --------------------------------------------------

@router.patch("/{case_id}/status")
def update_case_status(
    case_id: UUID,
    status: str,
):
    if status not in VALID_CASE_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    updated = db_update(
        table="skin_cases",
        filters={"id": str(case_id)},
        payload={
            "status": status,
            "updated_at": datetime.now(timezone.utc),
        }
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Case not found")

    audit_log(
        action="case_status_updated",
        details={"case_id": str(case_id), "status": status},
    )

    return updated[0]

# --------------------------------------------------
# ADD AI PREDICTION
# --------------------------------------------------

@router.post("/{case_id}/predictions")
def add_prediction(
    case_id: UUID,
    label: str,
    confidence: float,
    model_id: Optional[UUID] = None,
    bbox: Optional[dict] = None,
    is_primary: bool = False,
):
    if not (0.0 <= confidence <= 1.0):
        raise HTTPException(status_code=400, detail="Confidence out of range")

    prediction = db_insert(
        table="case_predictions",
        payload={
            "case_id": str(case_id),
            "label": label,
            "confidence": confidence,
            "bbox": bbox,
            "model_id": str(model_id) if model_id else None,
        }
    )

    if is_primary:
        db_update(
            table="skin_cases",
            filters={"id": str(case_id)},
            payload={
                "ai_primary_label": label,
                "ai_confidence": confidence,
                "ai_result": label,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    return prediction

# --------------------------------------------------
# ASSIGN DOCTOR
# --------------------------------------------------

@router.post("/{case_id}/assign")
def assign_doctor(
    case_id: UUID,
    doctor_id: UUID,
    assigned_by: UUID,
    reason: Optional[str] = None,
):
    assignment = db_insert(
        table="case_assignments",
        payload={
            "case_id": str(case_id),
            "doctor_id": str(doctor_id),
            "assigned_by": str(assigned_by),
            "reason": reason,
        }
    )

    db_update(
        table="skin_cases",
        filters={"id": str(case_id)},
        payload={
            "assigned_doctor": str(doctor_id),
            "status": CASE_PROCESSING,
            "updated_at": datetime.now(timezone.utc),
        }
    )

    audit_log(
        action="case_assigned",
        actor_id=str(assigned_by),
        details={
            "case_id": str(case_id),
            "doctor_id": str(doctor_id),
        },
    )

    return assignment
