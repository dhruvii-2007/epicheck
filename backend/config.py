import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

MODEL_PATH = os.getenv("MODEL_PATH", "models/epicheck_detect.pt")

STORAGE_BUCKET = os.getenv("SUPABASE_BUCKET", "case-images")

CONFIDENCE_THRESHOLD = 0.5
