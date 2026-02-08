import os
import onnxruntime as ort
import numpy as np
from app.logger import logger

# --------------------------------------------------
# MODEL PATHS (priority order)
# --------------------------------------------------
PRIMARY_MODEL_PATH = "app/ai/models/epicheck-ai.onnx"
FALLBACK_MODEL_PATH = "app/ai/models/best.onnx"

_session = None
_model_path = None


# --------------------------------------------------
# LOAD MODEL (ONCE)
# --------------------------------------------------
def _load_model():
    global _session, _model_path

    if _session:
        return _session

    if os.path.exists(PRIMARY_MODEL_PATH):
        _model_path = PRIMARY_MODEL_PATH
    elif os.path.exists(FALLBACK_MODEL_PATH):
        _model_path = FALLBACK_MODEL_PATH
    else:
        raise FileNotFoundError(
            "No AI model found. Expected epicheck-ai.onnx or best.onnx"
        )

    logger.info(f"Loading AI model: {_model_path}")

    _session = ort.InferenceSession(
        _model_path,
        providers=["CPUExecutionProvider"]
    )

    return _session


# --------------------------------------------------
# RUN INFERENCE
# --------------------------------------------------
def run_inference(image_array: np.ndarray) -> dict:
    """
    image_array: preprocessed numpy array ready for model
    """

    session = _load_model()

    input_name = session.get_inputs()[0].name
    output_names = [o.name for o in session.get_outputs()]

    outputs = session.run(
        output_names,
        {input_name: image_array}
    )

    # --------------------------------------------------
    # 🔽 ADAPT THIS TO YOUR MODEL OUTPUT FORMAT
    # --------------------------------------------------
    probabilities = outputs[0][0]

    confidence = float(np.max(probabilities))
    predicted_class = int(np.argmax(probabilities))

    return {
        "primary_label": predicted_class,
        "confidence": confidence,
        "model_used": os.path.basename(_model_path)
    }
