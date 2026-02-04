from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from ultralytics import YOLO
import io
import os
import urllib.request
import base64
import cv2
import numpy as np

# ================== CONFIG ==================
MODEL_DIR = "models"
TRAINED_MODEL = "epicheck_detect.pt"   # your trained model (may not exist yet)
FALLBACK_MODEL = "yolov8n.pt"          # small pretrained fallback
API_KEY = "nfvskelcmSDF@fnkewjdn5820ndsfjewER_fudwjkaty7247"

# URLs for fallback download
FALLBACK_URL = "https://github.com/ultralytics/assets/releases/download/v8.0/yolov8n.pt"

# Full paths
trained_path = os.path.join(MODEL_DIR, TRAINED_MODEL)
fallback_path = os.path.join(MODEL_DIR, FALLBACK_MODEL)

os.makedirs(MODEL_DIR, exist_ok=True)

# Download fallback model if missing
if not os.path.exists(fallback_path):
    print("⬇️ Downloading fallback YOLOv8n model...")
    urllib.request.urlretrieve(FALLBACK_URL, fallback_path)

# Decide which model to load
if os.path.exists(trained_path):
    print("✅ Loading trained model")
    model = YOLO(trained_path)
else:
    print("⚠️ Trained model not found, using fallback YOLOv8n")
    model = YOLO(fallback_path)

# ================== FastAPI ==================
app = FastAPI(title="Epicheck Detection API")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://epi-check.great-site.net",
        "https://epi-check.great-site.net",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "x-api-key"],
)

@app.get("/")
def health():
    return {"status": "Epicheck Detection API is running"}

def verify_api_key(request: Request, x_api_key: str = Header(None)):
    if request.method == "OPTIONS":
        return
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

# ================== ROUTES ==================
@app.post("/predict")
async def predict(file: UploadFile = File(...), _: None = Depends(verify_api_key)):
    # Read image
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    # YOLO inference with safe letterbox
    results = model.predict(
        source=image,
        imgsz=640,
        conf=0.25,
        device="cpu",
        stream=False,
        verbose=False
    )

    # Annotate image
    annotated = results[0].plot()  # numpy BGR array
    annotated_image = Image.fromarray(annotated[..., ::-1])  # Convert BGR → RGB

    # Encode annotated image to base64
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

    return {
        "count": len(detections),
        "detections": detections,
        "annotated_image": encoded_image
    }

# ================== RUN APP ==================
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))  # Render dynamically assigns PORT
    uvicorn.run("main:app", host="0.0.0.0", port=port)
