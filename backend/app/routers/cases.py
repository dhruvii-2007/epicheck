from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.auth import get_current_user
from app.supabase import supabase
from app.services.ai_client import run_inference, AIInferenceError
from app.schemas.cases import CaseCreate
from app.logger import logger

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("")
async def create_case(
    payload: CaseCreate,
    image: UploadFile = File(...),
    user=Depends(get_current_user),
):
    # --------------------------------------------------
    # 1. Authorization
    # --------------------------------------------------
    if user["role"] != "user":
        raise HTTPException(status_code=403, detail="Only users can create cases")

    # --------------------------------------------------
    # 2. Create skin case (authoritative)
    # --------------------------------------------------
    case_resp = (
        supabase.table("skin_cases")
        .insert(
            {
                "user_id": user["id"],
                "description": payload.description,
                "status": "submitted",
            }
        )
        .execute()
    )

    if not case_resp.data:
        raise HTTPException(status_code=500, detail="Failed to create case")

    case = case_resp.data[0]
    case_id = case["id"]

    # --------------------------------------------------
    # 3. Read image bytes
    # --------------------------------------------------
    try:
        image_bytes = await image.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image upload")

    # --------------------------------------------------
    # 4. Run AI inference (non-authoritative)
    # --------------------------------------------------
    try:
        ai_result = await run_inference(image_bytes)

        prediction = ai_result["prediction"]

        # Example severity extraction (adjust to your model)
        severity_score = float(max(prediction[0]))

        supabase.table("case_predictions").insert(
            {
                "case_id": case_id,
                "model_version": "best.onnx",
                "prediction": prediction,
                "severity_score": severity_score,
            }
        ).execute()

    except AIInferenceError as e:
        logger.error(f"AI inference failed for case {case_id}: {e}")

        # Case still exists; triggers & cron can handle retry/escalation
        supabase.table("skin_cases").update(
            {"status": "processing_failed"}
        ).eq("id", case_id).execute()

    # --------------------------------------------------
    # 5. Return case (never block user on AI)
    # --------------------------------------------------
    return {
        "case_id": case_id,
        "status": case["status"],
    }
