import onnxruntime as ort

_session = None

def get_session(model_path: str):
    global _session
    if _session is None:
        _session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"]
        )
    return _session
