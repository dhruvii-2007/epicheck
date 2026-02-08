from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.supabase_client import supabase

security = HTTPBearer(auto_error=True)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Authenticates user via Supabase JWT
    Loads profile
    Injects request.state.user and request.state.profile
    """

    token = credentials.credentials

    # --------------------------------------------------
    # Verify Supabase auth token
    # --------------------------------------------------
    try:
        auth_resp = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if not auth_resp or not auth_resp.user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    auth_user = auth_resp.user

    # Optional hard guard
    if not auth_user.email:
        raise HTTPException(status_code=401, detail="Invalid user account")

    # --------------------------------------------------
    # Fetch profile (RLS-aware)
    # --------------------------------------------------
    profile_resp = (
        supabase
        .table("profiles")
        .select("*")
        .eq("id", auth_user.id)
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )

    if not profile_resp.data:
        raise HTTPException(
            status_code=403,
            detail="Profile not found or deleted"
        )

    profile = profile_resp.data[0]

    # --------------------------------------------------
    # Status checks
    # --------------------------------------------------
    if profile.get("is_suspended"):
        raise HTTPException(
            status_code=403,
            detail="Account suspended"
        )

    # --------------------------------------------------
    # Inject into request state
    # --------------------------------------------------
    # Canonical user object = profile
    request.state.user = profile
    request.state.profile = profile
    request.state.auth = {
        "id": auth_user.id,
        "email": auth_user.email
    }

    return profile
