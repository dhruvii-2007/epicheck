# app/logger.py

from app.core_logger import logger

def request_log(
    user_id: str | None,
    ip_address: str | None,
    endpoint: str,
    method: str,
    status_code: int,
):
    """
    Application-level request logging.
    DB audit handled by triggers.
    """
    logger.info(
        "http_request",
        extra={
            "user_id": user_id,
            "ip_address": ip_address,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
        },
    )
