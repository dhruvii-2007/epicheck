import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "case-images")

MODEL_PATH = os.getenv("MODEL_PATH", "models/epicheck_detect.onnx")

CONFIDENCE_THRESHOLD = 0.5

# Fail fast
if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is not set")

if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is not set")

if not os.path.exists(MODEL_PATH):
    raise RuntimeError(f"Model file not found at {MODEL_PATH}")
