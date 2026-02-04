from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import os
import urllib.request
import base64
import numpy as np
import onnxruntime as ort
import cv2

# ================== CONFIG ==================
MODEL_DIR = "models"
MODEL_NAME = "epicheck_detect.onnx"  # ONNX model
# If missing, fallback to YOLOv8n just to have a model
MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt"


API_KEY = "nfvskelcmSDF@fnkewjdn5820ndsfjewER_fudwjkaty7247"

MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)
os.makedirs(MODEL_DIR, exist_ok=True)

# Download model if missing
if not os.path.exists(MODEL_PATH):
    print("⬇️ Downloading ONNX model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

# ================== FastAPI ==================
app = FastAPI(title="Epicheck Detection API")

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

# ================== ONNX Setup ==================
session = ort.InferenceSession(MODEL_PATH)

# Load class names from your trained model (example placeholder)
# Replace with actual class names used in training
CLASS_NAMES = [
    "eczema", "psoriasis", "ringworm", "lichen_planus", "seborrheic_keratoses"
]

# ================== ROUTES ==================
@app.post("/predict")
async def predict(file: UploadFile = File(...), _: None = Depends(verify_api_key)):
    # Read image
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_np = np.array(image)

    # Resize to 640x640 (YOLO standard)
    img_resized = cv2.resize(img_np, (640, 640))
    img_input = img_resized.astype(np.float32) / 255.0
    img_input = np.transpose(img_input, (2, 0, 1))  # HWC → CHW
    img_input = np.expand_dims(img_input, axis=0)    # batch dimension

    # Run ONNX inference
    outputs = session.run(None, {"images": img_input})

    # Parse ONNX outputs to boxes, confidence, class_id
    # YOLOv8 ONNX outputs: [batch, num_predictions, 6] → (x1, y1, x2, y2, conf, cls)
    boxes_raw = outputs[0][0]  # first image in batch
    boxes = []
    for b in boxes_raw:
        conf = float(b[4])
        if conf < 0.25:
            continue
        cls_id = int(b[5])
        x1, y1, x2, y2 = b[:4]
        boxes.append({
            "cls_id": cls_id,
            "conf": conf,
            "bbox": [x1, y1, x2, y2]
        })

    # Draw boxes on image
    annotated_image = img_np.copy()
    for b in boxes:
        cls_id = b["cls_id"]
        conf = b["conf"]
        x1, y1, x2, y2 = map(int, b["bbox"])
        label = f"{CLASS_NAMES[cls_id]} {conf:.2f}"
        cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0,255,0), 2)
        cv2.putText(annotated_image, label, (x1, max(y1-5,0)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

    # Convert annotated image to base64
    annotated_pil = Image.fromarray(annotated_image)
    buffer = io.BytesIO()
    annotated_pil.save(buffer, format="JPEG", quality=85)
    encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Prepare detections for API
    detections = []
    for b in boxes:
        cls_id = b["cls_id"]
        conf = b["conf"]
        detections.append({
            "class": CLASS_NAMES[cls_id],
            "confidence": round(conf, 4)
        })

    return {
        "count": len(detections),
        "detections": detections,
        "annotated_image": encoded_image
    }
