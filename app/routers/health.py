from fastapi import APIRouter
from app.supabase_client import supabase
from app.logger import logger

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """
    Render / uptime health check.
    Verifies backend is alive and DB is reachable.
    """
    db_ok = True

    try:
        supabase.table("feature_flags").select("key").limit(1).execute()
    except Exception as e:
        logger.error(f"Health DB check failed: {e}")
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "up" if db_ok else "down"
    }


@router.get("/version")
def version_info():
    """
    Returns backend version, active AI model and feature flags.
    """

    # Fetch active AI model
    model_response = (
        supabase
        .table("ai_models")
        .select("id, name, version, framework, deployed_at")
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    active_model = model_response.data[0] if model_response.data else None

    # Fetch feature flags
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

    return {
        "api": "Epicheck",
        "version": "1.0.0",
        "environment": "production",
        "ai_model": active_model,
        "feature_flags": feature_flags
    }
