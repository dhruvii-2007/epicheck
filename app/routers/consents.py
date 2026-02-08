from fastapi import APIRouter, Depends, Request
from app.core.dependencies import get_current_user
from app.supabase_client import supabase

router = APIRouter(prefix="/consents", tags=["Consents"])


@router.post("")
def add_consent(
    payload: dict,
    request: Request,
    profile=Depends(get_current_user)
):
    """
    Record user consent
    """
    consent = {
        "user_id": profile["id"],
        "consent_type": payload.get("consent_type"),
        "consent_version": payload.get("consent_version"),
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent")
    }

    supabase.table("user_consents").insert(consent).execute()

    return {"status": "consent_recorded"}


@router.get("")
def list_consents(profile=Depends(get_current_user)):
    """
    List user's consents
    """
    resp = (
        supabase
        .table("user_consents")
        .select("*")
        .eq("user_id", profile["id"])
        .execute()
    )

    return resp.data or []
