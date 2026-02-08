from fastapi import Depends, HTTPException, Request
from app.core.dependencies import get_current_user


def require_role(allowed_roles: list[str]):
    """
    Generic role guard.
    Must be used AFTER get_current_user has populated request.state.profile
    """
    def checker(
        request: Request,
        profile=Depends(get_current_user)
    ):
        role = profile.get("role")

        if role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions"
            )

        return profile

    return checker


# --------------------------------------------------
# Role-specific guards
# --------------------------------------------------

def require_user(profile=Depends(require_role(["user"]))):
    return profile


def require_doctor(profile=Depends(require_role(["doctor"]))):
    if profile.get("status") != "approved":
        raise HTTPException(
            status_code=403,
            detail="Doctor not verified"
        )
    return profile


def require_support(profile=Depends(require_role(["support"]))):
    return profile


def require_admin(profile=Depends(require_role(["admin"]))):
    return profile


def require_support_or_admin(
    profile=Depends(require_role(["support", "admin"]))
):
    return profile
