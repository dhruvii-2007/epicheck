from fastapi import FastAPI, UploadFile, File, Depends
from auth import get_current_user
from inference.detector import Detector
from services.severity import calculate_severity
from services.case_service import create_case
from config import MODEL_PATH
import numpy as np
from PIL import Image
import io

app = FastAPI(title="Epicheck API")

detector = Detector(MODEL_PATH)

@app.post("/api/v1/analyze")
async def analyze_case(
    file: UploadFile = File(...),
    symptoms: str = "",
    user = Depends(get_current_user)
):
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")
    image_np = np.array(image)

    predictions = detector.predict(image_np)

    if not predictions:
        return {"error": "No condition detected"}

    top = max(predictions, key=lambda x: x["confidence"])

    severity_score, risk, action = calculate_severity(
        symptoms.split(","),
        top["confidence"]
    )

    case = create_case(
        user.id,
        "uploaded_later",
        top["label"],
        top["confidence"],
        severity_score,
        risk,
        action
    )

    return {
        "case_id": case["id"],
        "prediction": top,
        "risk_level": risk,
        "action_plan": action,
        "disclaimer": "This is not a medical diagnosis"
    }
