from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from PIL import Image
from ultralytics import YOLO
import io
import os
import urllib.request
import base64

# ---------------- CONFIG ----------------
MODEL_DIR = "models"
MODEL_NAME = "epicheck_detect.pt"
MODEL_URL = "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt"

API_KEY = "nfvskelcmSDF@fnkewjdn5820ndsfjewER_fudwjkaty7247"
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)
# ----------------------------------------

app = FastAPI(title="Epicheck Detection API")

os.environ["ULTRALYTICS_SETTINGS"] = "False"
os.makedirs(MODEL_DIR, exist_ok=True)

if not os.path.exists(MODEL_PATH):
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

model = YOLO(MODEL_PATH)


@app.get("/")
def health():
    return {"status": "Epicheck Detection API is running"}


def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    _: None = verify_api_key
):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    results = model(image, conf=0.25)

    # 🔹 Get annotated image (YOLO draws boxes)
    annotated = results[0].plot()  # numpy array (BGR)

    # Convert to PIL Image
    annotated_image = Image.fromarray(annotated[..., ::-1])

    # Convert image → base64
    buffer = io.BytesIO()
    annotated_image.save(buffer, format="JPEG")
    encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")

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
