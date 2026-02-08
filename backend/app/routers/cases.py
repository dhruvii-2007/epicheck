from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user
from app.schemas.cases import CaseCreate
from app.supabase import supabase

router = APIRouter(prefix="/cases", tags=["cases"])

@router.post("")
def create_case(payload: CaseCreate, user=Depends(get_current_user)):
    if user["role"] != "user":
        raise HTTPException(403)

    return (
        supabase.table("skin_cases")
        .insert({
            "user_id": user["id"],
            "description": payload.description,
            "status": "submitted"
        })
        .execute()
        .data
    )
