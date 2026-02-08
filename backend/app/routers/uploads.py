from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4
from app.auth import get_current_user
from app.supabase import supabase

router = APIRouter(prefix="/uploads", tags=["uploads"])

@router.post("/cases/{case_id}")
def get_upload_url(case_id: str, user=Depends(get_current_user)):
    case = (
        supabase.table("skin_cases")
        .select("id")
        .eq("id", case_id)
        .eq("user_id", user["id"])
        .single()
        .execute()
        .data
    )

    if not case:
        raise HTTPException(404)

    path = f"{case_id}/{uuid4()}.jpg"
    return supabase.storage.from_("case-images").create_signed_upload_url(path)
