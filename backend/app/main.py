from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .config import API_VERSION
from .supabase_client import supabase
from .inference import predict_stub
from .validators import validate_image
from .logger import logger
from .auth import get_current_user

load_dotenv()

app = FastAPI(
    title="Epicheck Backend",
    version=API_VERSION
)

# ---------------- CORS ----------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-infinityfree-site.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- HEALTH CHECK ----------------
@app.get("/health")
def health_check():
    return {"status": "ok"}

# ---------------- PREDICT API ----------------
@app.post(f"/{API_VERSION}/predict")
async def predict(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        contents = await file.read()
        validate_image(file, len(contents))

        disease, confidence = predict_stub()

        supabase.table("reports").insert({
            "user_id": current_user["sub"],
            "disease": disease,
            "confidence": confidence
        }).execute()

        logger.info(f"Prediction stored for user {current_user['sub']}")

        return {
            "success": True,
            "disease": disease,
            "confidence": confidence
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )
