import httpx
import os

AI_WORKER_URL = os.getenv("AI_WORKER_URL")
AI_API_KEY = os.getenv("AI_API_KEY")
AI_TIMEOUT = 20.0


class AIInferenceError(Exception):
    pass


async def run_inference(image_bytes: bytes):
    if not AI_WORKER_URL or not AI_API_KEY:
        raise RuntimeError("AI worker not configured")

    async with httpx.AsyncClient(timeout=AI_TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{AI_WORKER_URL}/predict",
                headers={
                    "X-AI-KEY": AI_API_KEY
                },
                files={
                    "file": ("image.jpg", image_bytes, "image/jpeg")
                },
            )
        except httpx.RequestError as e:
            raise AIInferenceError(f"AI worker unreachable: {e}")

    if resp.status_code != 200:
        raise AIInferenceError(
            f"AI worker error {resp.status_code}: {resp.text}"
        )

    return resp.json()
