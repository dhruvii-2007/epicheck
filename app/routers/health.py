from datetime import datetime
from fastapi import APIRouter

from app.supabase_client import supabase
from app.config import ENVIRONMENT

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """
    Render / uptime health check.
    Verifies backend is alive and DB is reachable.
    """

    db_ok = True

    try:
        # lightweight DB ping
        supabase.table("feature_flags").select("key").limit(1).execute()
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "up" if db_ok else "down",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/version")
def version_info():
    """
    Returns backend version, active AI model and feature flags.
    """

    # --------------------------------------------------
    # Active AI model
    # --------------------------------------------------
    try:
        model_response = (
            supabase
            .table("ai_models")
            .select("id, name, version, framework, deployed_at")
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        active_model = model_response.data[0] if model_response.data else None
    except Exception:
        active_model = None

    # --------------------------------------------------
    # Feature flags
    # --------------------------------------------------
    try:
        flags_response = (
            supabase
            .table("feature_flags")
            .select("key, enabled")
            .execute()
        )
        feature_flags = {
            flag["key"]: flag["enabled"]
            for flag in (flags_response.data or [])
        }
    except Exception:
        feature_flags = {}

    return {
        "api": "Epicheck",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "ai_model": active_model,
        "feature_flags": feature_flags
    }
