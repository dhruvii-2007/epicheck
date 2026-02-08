from fastapi import APIRouter, HTTPException
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from app.supabase_client import db_select, db_insert, db_update
from app.config import (
    REVIEW_APPROVED,
    REVIEW_REJECTED,
    REVIEW_NEEDS_MORE_INFO,
    VALID_REVIEW_DECISIONS,
    CASE_REVIEWED,
)
from app.logger import audit_log

router = APIRouter()

# --------------------------------------------------
# GET DOCTOR PROFILE
# --------------------------------------------------

@router.get("/{doctor_id}")
def get_doctor_profile(doctor_id: UUID):
    profile = db_select(
        table="profiles",
        filters={"id": str(doctor_id)},
        single=True
    )

    if not profile or profile["role"] != "doctor":
        raise HTTPException(status_code=404, detail="Doctor not found")

    return profile

# --------------------------------------------------
# SUBMIT DOCTOR VERIFICATION
# --------------------------------------------------

@router.post("/{doctor_id}/verify")
def submit_verification(
    doctor_id: UUID,
    document_url: str,
    submitted_by: UUID,
):
    verification = db_insert(
        table="doctor_verifications",
        payload={
            "doctor_id": str(doctor_id),
            "verified_by": str(submitted_by),
            "verification_status": "pending",
            "document_url": document_url,
            "verified_at": datetime.now(timezone.utc),
        }
    )

    audit_log(
        action="doctor_verification_submitted",
        actor_id=str(doctor_id),
        actor_role="doctor",
        details={"verification_id": verification["id"]},
    )

    return verification

# --------------------------------------------------
# REVIEW CASE
# --------------------------------------------------

@router.post("/cases/{case_id}/review")
def review_case(
    case_id: UUID,
    doctor_id: UUID,
    decision: str,
    review: Optional[str] = None,
):
    if decision not in VALID_REVIEW_DECISIONS:
        raise HTTPException(status_code=400, detail="Invalid decision")

    case = db_select(
        table="skin_cases",
        filters={"id": str(case_id)},
        single=True
    )

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.get("assigned_doctor") != str(doctor_id):
        raise HTTPException(status_code=403, detail="Doctor not assigned to this case")

    doctor_review = db_insert(
        table="doctor_reviews",
        payload={
            "case_id": str(case_id),
            "doctor_id": str(doctor_id),
            "decision": decision,
            "review": review,
            "created_at": datetime.now(timezone.utc),
        }
    )

    db_update(
        table="skin_cases",
        filters={"id": str(case_id)},
        payload={
            "reviewed": True,
            "status": CASE_REVIEWED,
            "updated_at": datetime.now(timezone.utc),
        }
    )

    audit_log(
        action="case_reviewed",
        actor_id=str(doctor_id),
        actor_role="doctor",
        details={
            "case_id": str(case_id),
            "decision": decision,
        },
    )

    return doctor_review
