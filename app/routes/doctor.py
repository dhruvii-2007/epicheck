from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from ..auth import require_approved_doctor
from ..supabase_client import (
    db_select,
    db_insert,
    db_update
)
from ..config import (
    CASE_REVIEWED,
    AUDIT_REVIEW_CASE,
    AUDIT_ASSIGN_CASE,
    REVIEW_DECISIONS
)

router = APIRouter(
    prefix="/v1/doctor",
    tags=["Doctor"]
)

# --------------------------------------------------
# GET ASSIGNED CASES
# --------------------------------------------------
@router.get("/cases")
def get_assigned_cases(
    doctor=Depends(require_approved_doctor)
):
    cases = db_select(
        table="skin_cases",
        filters={
            "assigned_doctor": doctor["sub"],
            "deleted_at": None
        }
    )

    return {"cases": cases}


# --------------------------------------------------
# GET SINGLE CASE DETAILS
# --------------------------------------------------
@router.get("/cases/{case_id}")
def get_case_details(
    case_id: str,
    doctor=Depends(require_approved_doctor)
):
    case = db_select(
        table="skin_cases",
        filters={"id": case_id},
        single=True
    )

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.get("assigned_doctor") != doctor["sub"]:
        raise HTTPException(status_code=403, detail="Not assigned to this case")

    predictions = db_select(
        table="case_predictions",
        filters={"case_id": case_id}
    )

    symptoms = db_select(
        table="case_symptoms",
        filters={"case_id": case_id}
    )

    return {
        "case": case,
        "predictions": predictions,
        "symptoms": symptoms
    }


# --------------------------------------------------
# SUBMIT REVIEW
# --------------------------------------------------
@router.post("/review/{case_id}")
def review_case(
    case_id: str,
    decision: str = Query(...),
    review: str | None = None,
    doctor=Depends(require_approved_doctor)
):
    if decision not in REVIEW_DECISIONS:
        raise HTTPException(status_code=400, detail="Invalid review decision")

    case = db_select(
        table="skin_cases",
        filters={"id": case_id},
        single=True
    )

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.get("assigned_doctor") != doctor["sub"]:
        raise HTTPException(status_code=403, detail="Not assigned to this case")

    # Save doctor review
    db_insert(
        table="doctor_reviews",
        payload={
            "case_id": case_id,
            "doctor_id": doctor["sub"],
            "decision": decision,
            "review": review,
            "created_at": datetime.utcnow().isoformat()
        }
    )

    # Update case
    db_update(
        table="skin_cases",
        payload={
            "reviewed": True,
            "status": CASE_REVIEWED,
            "updated_at": datetime.utcnow().isoformat()
        },
        filters={"id": case_id}
    )

    # Audit log
    db_insert(
        table="audit_logs",
        payload={
            "actor_id": doctor["sub"],
            "actor_role": "doctor",
            "action": AUDIT_REVIEW_CASE,
            "details": {
                "case_id": case_id,
                "decision": decision
            },
            "created_at": datetime.utcnow().isoformat()
        }
    )

    return {"reviewed": True}


# --------------------------------------------------
# VIEW OWN REVIEWS
# --------------------------------------------------
@router.get("/reviews")
def get_my_reviews(
    doctor=Depends(require_approved_doctor)
):
    reviews = db_select(
        table="doctor_reviews",
        filters={"doctor_id": doctor["sub"]}
    )

    return {"reviews": reviews}


# --------------------------------------------------
# ACCEPT CASE ASSIGNMENT (OPTIONAL SAFETY)
# --------------------------------------------------
@router.post("/cases/{case_id}/accept")
def accept_case(
    case_id: str,
    doctor=Depends(require_approved_doctor)
):
    case = db_select(
        table="skin_cases",
        filters={"id": case_id},
        single=True
    )

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.get("assigned_doctor") != doctor["sub"]:
        raise HTTPException(status_code=403, detail="Not assigned to this case")

    db_insert(
        table="audit_logs",
        payload={
            "actor_id": doctor["sub"],
            "actor_role": "doctor",
            "action": AUDIT_ASSIGN_CASE,
            "details": {"case_id": case_id},
            "created_at": datetime.utcnow().isoformat()
        }
    )

    return {"accepted": True}
