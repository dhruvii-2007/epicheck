import random

# --------------------------------------------------
# AI INFERENCE STUB
# --------------------------------------------------
# This will be replaced by the ONNX / Torch model later.
# API contract WILL NOT change when AI is plugged in.
# --------------------------------------------------

DISEASE_LABELS = [
    "melanoma",
    "nevus",
    "seborrheic_keratosis",
    "basal_cell_carcinoma",
    "benign"
]


def predict_stub():
    """
    Temporary AI prediction stub.
    Returns:
        (label: str, confidence: float)
    """

    label = random.choice(DISEASE_LABELS)
    confidence = round(random.uniform(0.70, 0.99), 2)

    return label, confidence
