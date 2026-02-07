from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from ..auth import require_approved_doctor
from ..supabase_client import db_select, db_insert, db_update
from ..config import (
    CASE_REVIEWED,
    AUDIT_REVIEW_CASE,
    AUDIT_ASSIGN_CASE,
    REVIEW_DECISIONS
)

router = APIRouter(tags=["Doctor"])

# --------------------------------------------------
# GET ASSIGNED CASES
# --------------------------------------------------
@router.get("/doctor/cases")
def get_assigned_cases(doctor=Depends(require_approved_doctor)):
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
@router.get("/doctor/cases/{case_id}")
def get_case_details(case_id: str, doctor=Depends(require_approved_doctor)):
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
@router.post("/doctor/cases/{case_id}/review")
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

    if case.get("reviewed"):
        raise HTTPException(status_code=409, detail="Case already reviewed")

    review_row = db_insert(
        table="doctor_reviews",
        payload={
            "case_id": case_id,
            "doctor_id": doctor["sub"],
            "decision": decision,
            "review": review,
            "created_at": datetime.utcnow().isoformat()
        }
    )

    db_update(
        table="skin_cases",
        payload={
            "reviewed": True,
            "status": CASE_REVIEWED,
            "updated_at": datetime.utcnow().isoformat()
        },
        filters={"id": case_id}
    )

    db_insert(
        table="audit_logs",
        payload={
            "actor_id": doctor["sub"],
            "actor_role": "doctor",
            "action": AUDIT_REVIEW_CASE,
            "target_table": "skin_cases",
            "target_id": case_id,
            "details": {
                "decision": decision,
                "review_id": review_row["id"]
            },
            "created_at": datetime.utcnow().isoformat()
        }
    )

    return {"reviewed": True}


# --------------------------------------------------
# VIEW OWN REVIEWS
# --------------------------------------------------
@router.get("/doctor/reviews")
def get_my_reviews(doctor=Depends(require_approved_doctor)):
    reviews = db_select(
        table="doctor_reviews",
        filters={"doctor_id": doctor["sub"]}
    )
    return {"reviews": reviews}


# --------------------------------------------------
# ACCEPT CASE ASSIGNMENT
# --------------------------------------------------
@router.post("/doctor/cases/{case_id}/accept")
def accept_case(case_id: str, doctor=Depends(require_approved_doctor)):
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
            "target_table": "skin_cases",
            "target_id": case_id,
            "details": {"accepted": True},
            "created_at": datetime.utcnow().isoformat()
        }
    )

    return {"accepted": True}
