from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from app.core.dependencies import get_current_user
from app.supabase_client import supabase
from app.ai.inference import run_inference
from app.services.audit import log_audit_event
from app.services.notifications import create_notification

router = APIRouter(prefix="/cases", tags=["AI"])


# --------------------------------------------------
# TRIGGER AI ANALYSIS
# --------------------------------------------------
@router.post("/{case_id}/analyze")
def analyze_case(
    case_id: str,
    profile=Depends(get_current_user)
):
    """
    Run AI inference on a case
    """

    # --------------------------------------------------
    # Fetch case (ownership + state)
    # --------------------------------------------------
    case_resp = (
        supabase
        .table("skin_cases")
        .select(
            "id, status, user_id"
        )
        .eq("id", case_id)
        .eq("user_id", profile["id"])
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )

    if not case_resp.data:
        raise HTTPException(status_code=404, detail="Case not found")

    case = case_resp.data[0]

    if case["status"] != "submitted":
        raise HTTPException(
            status_code=400,
            detail="Case cannot be analyzed in current state"
        )

    # --------------------------------------------------
    # Fetch case image (private storage path)
    # --------------------------------------------------
    file_resp = (
        supabase
        .table("case_files")
        .select("storage_path")
        .eq("case_id", case_id)
        .eq("marked_for_deletion", False)
        .limit(1)
        .execute()
    )

    if not file_resp.data:
        raise HTTPException(status_code=400, detail="No case image uploaded")

    storage_path = file_resp.data[0]["storage_path"]

    # --------------------------------------------------
    # Lock case
    # --------------------------------------------------
    supabase.table("skin_cases").update({
        "status": "processing",
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", case_id).execute()

    # --------------------------------------------------
    # Load active AI model
    # --------------------------------------------------
    model_resp = (
        supabase
        .table("ai_models")
        .select("id, name, version")
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    if not model_resp.data:
        supabase.table("skin_cases").update({
            "status": "submitted"
        }).eq("id", case_id).execute()

        raise HTTPException(status_code=500, detail="No active AI model")

    model = model_resp.data[0]

    # --------------------------------------------------
    # Run inference (guarded)
    # --------------------------------------------------
    try:
        result = run_inference(storage_path)
    except Exception as e:
        supabase.table("skin_cases").update({
            "status": "submitted"
        }).eq("id", case_id).execute()

        raise HTTPException(status_code=500, detail="AI inference failed")

    # --------------------------------------------------
    # Store prediction
    # --------------------------------------------------
    supabase.table("case_predictions").insert({
        "case_id": case_id,
        "model_id": model["id"],
        "primary_label": result["primary_label"],
        "secondary_labels": result.get("secondary_labels"),
        "confidence": result["confidence"],
        "severity_score": result.get("severity_score"),
        "risk_level": result.get("risk_level"),
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    # --------------------------------------------------
    # Update case
    # --------------------------------------------------
    supabase.table("skin_cases").update({
        "ai_primary_label": result["primary_label"],
        "ai_secondary_labels": result.get("secondary_labels"),
        "ai_confidence": result["confidence"],
        "severity_score": result.get("severity_score"),
        "risk_level": result.get("risk_level"),
        "status": "reviewed",
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", case_id).execute()

    # --------------------------------------------------
    # Audit + notification
    # --------------------------------------------------
    log_audit_event(
        actor_id=profile["id"],
        action="ai_analysis_completed",
        target_table="skin_cases",
        target_id=case_id,
        metadata={
            "model_id": model["id"],
            "model_version": model["version"]
        }
    )

    create_notification(
        user_id=profile["id"],
        title="AI analysis completed",
        message="Your skin case has been analyzed by our AI system.",
        notif_type="ai_completed",
        action_url=f"/cases/{case_id}"
    )

    return {
        "status": "completed",
        "ai_result": result
    }


# --------------------------------------------------
# GET CASE PREDICTIONS
# --------------------------------------------------
@router.get("/{case_id}/predictions")
def get_case_predictions(
    case_id: str,
    profile=Depends(get_current_user)
):
    """
    Return all AI predictions for a case
    """

    case_resp = (
        supabase
        .table("skin_cases")
        .select("id")
        .eq("id", case_id)
        .eq("user_id", profile["id"])
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )

    if not case_resp.data:
        raise HTTPException(status_code=404, detail="Case not found")

    preds = (
        supabase
        .table("case_predictions")
        .select("*")
        .eq("case_id", case_id)
        .is_("deleted_at", None)
        .order("created_at", desc=True)
        .execute()
    )

    return preds.data or []
