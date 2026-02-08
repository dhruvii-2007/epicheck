from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user
from app.schemas.reviews import ReviewCreate
from app.supabase import supabase

router = APIRouter(prefix="/doctor", tags=["doctor"])

@router.post("/reviews")
def submit_review(payload: ReviewCreate, user=Depends(get_current_user)):
    if user["role"] != "doctor":
        raise HTTPException(403)

    return (
        supabase.table("doctor_reviews")
        .insert({
            "doctor_id": user["id"],
            "case_id": payload.case_id,
            "notes": payload.notes,
            "decision": payload.decision
        })
        .execute()
        .data
    )
