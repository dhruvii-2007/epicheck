from fastapi import Depends, HTTPException, Request

# --------------------------------------------------
# Core role guard
# --------------------------------------------------

def require_role(allowed_roles: list[str]):
    """
    Generic role-based access control.
    Expects request.state.user to be populated by auth middleware.
    """
    def checker(request: Request):
        user = getattr(request.state, "user", None)

        if not user:
            raise HTTPException(status_code=401, detail="Unauthorized")

        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")

        return user

    return checker


# --------------------------------------------------
# Specific role guards
# --------------------------------------------------

def require_admin(user=Depends(require_role(["admin"]))):
    return user


def require_support(user=Depends(require_role(["support", "admin"]))):
    return user


def require_doctor(user=Depends(require_role(["doctor", "admin"]))):
    """
    Doctor must be verified unless admin.
    """
    if user["role"] == "doctor" and user.get("verification_status") != "approved":
        raise HTTPException(
            status_code=403,
            detail="Doctor not verified"
        )
    return user
