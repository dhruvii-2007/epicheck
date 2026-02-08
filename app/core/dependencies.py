from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.supabase_client import supabase

security = HTTPBearer()


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        user = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not user or not user.user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # fetch profile
    profile_resp = (
        supabase
        .table("profiles")
        .select("*")
        .eq("id", user.user.id)
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )

    if not profile_resp.data:
        raise HTTPException(status_code=403, detail="Profile not found or deleted")

    profile = profile_resp.data[0]

    if profile.get("is_suspended"):
        raise HTTPException(status_code=403, detail="Account suspended")

    request.state.user = user.user
    request.state.profile = profile

    return profile
