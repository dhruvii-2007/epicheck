from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .config import API_VERSION, ALLOWED_ORIGINS
from .auth import get_current_user
from .doctor import get_current_doctor, get_assigned_cases
from .validators import validate_image
from .inference import predict_stub
from .supabase_client import supabase
from .logger import logger

load_dotenv()

app = FastAPI(
    title="Epicheck API",
    version=API_VERSION
)

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- HEALTH ----------------
@app.get("/health")
def health():
    return {"status": "ok"}

# ---------------- USER PREDICT ----------------
@app.post(f"/{API_VERSION}/predict")
async def predict(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    contents = await file.read()
    validate_image(file, len(contents))

    disease, confidence = predict_stub()

    supabase.table("skin_cases").insert({
        "user_id": current_user["id"],
        "ai_primary_label": disease,
        "ai_confidence": confidence,
        "status": "submitted"
    }).execute()

    logger.info(f"Prediction created for user {current_user['id']}")

    return {
        "success": True,
        "label": disease,
        "confidence": confidence
    }

# ---------------- DOCTOR CASE LIST ----------------
@app.get(f"/{API_VERSION}/doctor/cases")
def doctor_cases(
    doctor=Depends(get_current_doctor)
):
    cases = get_assigned_cases(doctor)
    return {"cases": cases}
