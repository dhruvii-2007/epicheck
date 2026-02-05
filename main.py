from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from ultralytics import YOLO
import io
import os
import base64

from supabase_client import supabase
from auth import get_current_user

# ================== CONFIG ==================
MODEL_DIR = "models"
TRAINED_ONNX = "epicheck_detect.onnx"
FALLBACK_MODEL = "yolov8n.pt"

trained_path = os.path.join(MODEL_DIR, TRAINED_ONNX)
fallback_path = os.path.join(MODEL_DIR, FALLBACK_MODEL)

os.makedirs(MODEL_DIR, exist_ok=True)

# ================== MODEL LOADING ==================
model = None

if os.path.exists(trained_path):
    print(f"✅ Loading trained ONNX model: {TRAINED_ONNX}")
    model = YOLO(trained_path)
elif os.path.exists(fallback_path):
    print("⚠️ Trained model not found — using fallback YOLOv8n")
    model = YOLO(fallback_path)
else:
    print("❌ No model available! Add epicheck_detect.onnx or yolov8n.pt")
    model = None

# ================== FASTAPI ==================
app = FastAPI(title="Epicheck Detection API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://epi-check.great-site.net",
        "https://epi-check.great-site.net",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ================== HEALTH ==================
@app.get("/")
def health():
    return {"status": "Epicheck Detection API is running"}

# ================== PREDICT ==================
@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    if model is None:
        raise HTTPException(status_code=500, detail="No model loaded")

    # Read image
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # YOLO inference (UNCHANGED)
    results = model.predict(
        source=image,
        imgsz=640,
        conf=0.25,
        device="cpu",  # Render free tier
        stream=False,
        verbose=False
    )

    # Annotated image
    annotated = results[0].plot()
    annotated_image = Image.fromarray(annotated[..., ::-1])

    buffer = io.BytesIO()
    annotated_image.save(buffer, format="JPEG", quality=85)
    encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Parse detections
    detections = []
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        cls_name = model.names[cls_id]
        detections.append({
            "class": cls_name,
            "confidence": round(conf, 4)
        })

    # Pick top detection (if any)
    top_class = detections[0]["class"] if detections else "unknown"
    top_conf = detections[0]["confidence"] if detections else 0.0

    # ================== STORE IN SUPABASE ==================
    supabase.table("skin_cases").insert({
        "user_id": user.id,
        "ai_result": top_class,
        "ai_confidence": top_conf,
        "status": "ai_done"
    }).execute()

    # ================== RESPONSE ==================
    return {
        "count": len(detections),
        "detections": detections,
        "annotated_image": encoded_image
    }

# ================== LOCAL RUN ==================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
