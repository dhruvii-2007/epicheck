import os
import jwt
from fastapi import Depends, HTTPException, Request, status
from dotenv import load_dotenv

from .supabase_client import db_select
from .config import (
    ROLE_USER,
    ROLE_DOCTOR,
    ROLE_ADMIN,
    STATUS_APPROVED
)

load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

if not SUPABASE_JWT_SECRET:
    raise RuntimeError("SUPABASE_JWT_SECRET not set")


# --------------------------------------------------
# CORE JWT DECODER
# --------------------------------------------------

def get_current_user(request: Request):
    auth = request.headers.get("Authorization")

    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token"
        )

    token = auth.replace("Bearer ", "")

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    profile = db_select(
        table="profiles",
        filters={"id": user_id},
        single=True
    )

    if not profile:
        raise HTTPException(status_code=403, detail="Profile not found")

    if profile.get("is_suspended"):
        raise HTTPException(
            status_code=403,
            detail="Account suspended"
        )

    return {
        "sub": user_id,
        "email": profile.get("email"),
        "role": profile.get("role"),
        "status": profile.get("status")
    }


# --------------------------------------------------
# ROLE GUARDS
# --------------------------------------------------

def require_user(user=Depends(get_current_user)):
    if user["role"] not in [ROLE_USER, ROLE_DOCTOR, ROLE_ADMIN]:
        raise HTTPException(status_code=403, detail="User access required")
    return user


def require_admin(user=Depends(get_current_user)):
    if user["role"] != ROLE_ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_doctor(user=Depends(get_current_user)):
    if user["role"] != ROLE_DOCTOR:
        raise HTTPException(status_code=403, detail="Doctor access required")
    return user


def require_approved_doctor(user=Depends(get_current_user)):
    if user["role"] != ROLE_DOCTOR or user["status"] != STATUS_APPROVED:
        raise HTTPException(
            status_code=403,
            detail="Approved doctor access required"
        )
    return user
