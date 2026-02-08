import onnxruntime as ort
import numpy as np
import requests
from io import BytesIO
from PIL import Image


MODEL_PATH = "app/ai/models/epicheck.onnx"


def preprocess_image(image_url: str) -> np.ndarray:
    """
    Download and preprocess image for ONNX model
    """
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content)).convert("RGB")
    image = image.resize((224, 224))

    img_array = np.array(image).astype("float32") / 255.0
    img_array = np.transpose(img_array, (2, 0, 1))  # CHW
    img_array = np.expand_dims(img_array, axis=0)   # NCHW

    return img_array


def run_inference(image_url: str) -> dict:
    """
    Run ONNX inference and return structured output
    """
    session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name

    input_tensor = preprocess_image(image_url)
    outputs = session.run(None, {input_name: input_tensor})[0][0]

    labels = ["melanoma", "nevus", "benign_keratosis"]
    confidences = {labels[i]: float(outputs[i]) for i in range(len(labels))}

    primary_label = max(confidences, key=confidences.get)
    confidence = confidences[primary_label]

    severity_score = confidence * 10
    risk_level = "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low"

    return {
        "primary_label": primary_label,
        "secondary_labels": confidences,
        "confidence": confidence,
        "severity_score": severity_score,
        "risk_level": risk_level
    }
