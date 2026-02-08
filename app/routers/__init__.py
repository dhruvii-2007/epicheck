# app/routers/__init__.py

from .auth import router as auth
from .cases import router as cases
from .doctor import router as doctors
from .notifications import router as notifications
from .tickets import router as tickets

__all__ = [
    "auth",
    "cases",
    "doctors",
    "notifications",
    "tickets",
]
