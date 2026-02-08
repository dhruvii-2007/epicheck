from fastapi import APIRouter, HTTPException
from app.supabase_client import db_select

router = APIRouter()

@router.post("/login")
def login(email: str):
    user = db_select("users", {"email": email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")
    return user[0]
