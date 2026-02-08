from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user
from app.supabase import supabase

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/cases/{case_id}/assign")
def assign_case(case_id: str, doctor_id: str, user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(403)

    return (
        supabase.table("skin_cases")
        .update({"assigned_doctor": doctor_id})
        .eq("id", case_id)
        .execute()
    )
