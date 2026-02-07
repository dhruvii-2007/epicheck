import os
import jwt
from fastapi import Depends, HTTPException, Header
from .supabase_client import supabase

JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

if not JWT_SECRET:
    raise RuntimeError("SUPABASE_JWT_SECRET not set")


def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    profile = (
        supabase
        .table("profiles")
        .select("*")
        .eq("id", user_id)
        .single()
        .execute()
    )

    if not profile.data:
        raise HTTPException(status_code=403, detail="Profile not found")

    if profile.data["role"] != "user":
        raise HTTPException(status_code=403, detail="User role required")

    return profile.data
