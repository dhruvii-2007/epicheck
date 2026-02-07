import numpy as np

LABELS = [
    "melanoma",
    "nevus",
    "basal_cell_carcinoma",
    "eczema",
    "psoriasis",
    "benign"
]

def postprocess(output):
    probs = softmax(output[0])
    idx = int(np.argmax(probs))
    return {
        "label": LABELS[idx],
        "confidence": float(probs[idx])
    }

def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()
