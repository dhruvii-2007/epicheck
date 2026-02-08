from fastapi import Depends, HTTPException
from app.core.dependencies import get_current_user


def require_doctor(profile=Depends(get_current_user)):
    if profile["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Doctor access required")
    if profile["status"] != "approved":
        raise HTTPException(status_code=403, detail="Doctor not verified")
    return profile


def require_admin(profile=Depends(get_current_user)):
    if profile["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return profile
from fastapi import Depends, HTTPException
from app.core.dependencies import get_current_user


def require_doctor(profile=Depends(get_current_user)):
    if profile["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Doctor access required")
    if profile["status"] != "approved":
        raise HTTPException(status_code=403, detail="Doctor not verified")
    return profile


def require_admin(profile=Depends(get_current_user)):
    if profile["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return profile


def require_support_or_admin(profile=Depends(get_current_user)):
    if profile["role"] not in ["support", "admin"]:
        raise HTTPException(status_code=403, detail="Support access required")
    return profile
from fastapi import Depends, HTTPException, Request

def require_role(allowed_roles: list[str]):
    def checker(request: Request):
        user = getattr(request.state, "user", None)

        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")

        return user
    return checker


def require_admin(user=Depends(require_role(["admin"]))):
    return user


def require_doctor(user=Depends(require_role(["doctor", "admin"]))):
    return user


def require_support(user=Depends(require_role(["support", "admin"]))):
    return user
