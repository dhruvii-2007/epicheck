from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.core.dependencies import get_current_user
from app.supabase_client import supabase
from app.ai.inference import run_inference

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

    # fetch case
    case_resp = (
        supabase
        .table("skin_cases")
        .select("*")
        .eq("id", case_id)
        .eq("user_id", profile["id"])
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )

    if not case_resp.data:
        raise HTTPException(status_code=404, detail="Case not found")

    case = case_resp.data[0]

    if not case.get("image_url"):
        raise HTTPException(status_code=400, detail="No image uploaded")

    # lock case
    supabase.table("skin_cases").update({
        "status": "processing",
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", case_id).execute()

    # load active AI model
    model_resp = (
        supabase
        .table("ai_models")
        .select("id, name, version")
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    if not model_resp.data:
        raise HTTPException(status_code=500, detail="No active AI model")

    model = model_resp.data[0]

    # run inference
    result = run_inference(case["image_url"])

    # insert prediction
    supabase.table("case_predictions").insert({
        "case_id": case_id,
        "label": result["primary_label"],
        "confidence": result["confidence"],
        "model_id": model["id"]
    }).execute()

    # update case with AI results
    supabase.table("skin_cases").update({
        "ai_primary_label": result["primary_label"],
        "ai_secondary_labels": result["secondary_labels"],
        "ai_confidence": result["confidence"],
        "severity_score": result["severity_score"],
        "risk_level": result["risk_level"],
        "status": "reviewed",
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", case_id).execute()

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

    # verify ownership
    case_resp = (
        supabase
        .table("skin_cases")
        .select("id")
        .eq("id", case_id)
        .eq("user_id", profile["id"])
        .is_("deleted_at", None)
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
        .execute()
    )

    return preds.data or []
