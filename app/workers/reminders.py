import datetime
from app.supabase_client import (
    db_select,
    db_insert,
    db_update
)
from app.logger import logger
from app.config import (
    CASE_SUBMITTED,
    CASE_PROCESSING,
    NOTIFY_CASE,
    NOTIFY_SYSTEM
)

# --------------------------------------------------
# REMINDER CONFIG
# --------------------------------------------------

REVIEW_REMINDER_HOURS = 24
UNASSIGNED_REMINDER_HOURS = 12


# --------------------------------------------------
# REMINDER JOB
# --------------------------------------------------

def send_reminders():
    """
    Sends reminder notifications for:
    - Unassigned skin cases
    - Pending doctor reviews
    """

    now = datetime.datetime.utcnow()
    job_started_at = now.isoformat()

    try:
        # --------------------------------------------------
        # UNASSIGNED CASE REMINDERS (ADMIN)
        # --------------------------------------------------

        unassigned_cases = db_select(
            table="skin_cases",
            filters={
                "status": CASE_SUBMITTED,
                "assigned_doctor": None
            }
        )

        for case in unassigned_cases:
            created_at = datetime.datetime.fromisoformat(case["created_at"])
            age_hours = (now - created_at).total_seconds() / 3600

            if age_hours >= UNASSIGNED_REMINDER_HOURS:
                admins = db_select(
                    table="profiles",
                    filters={"role": "admin"}
                )

                for admin in admins:
                    db_insert(
                        table="notifications",
                        payload={
                            "user_id": admin["id"],
                            "title": "Unassigned Case Pending",
                            "message": (
                                "A skin case has not been assigned to any doctor "
                                f"for over {UNASSIGNED_REMINDER_HOURS} hours."
                            ),
                            "type": NOTIFY_ADMIN,
                            "action_url": f"/admin/cases/{case['id']}"
                        }
                    )

        # --------------------------------------------------
        # PENDING REVIEW REMINDERS (DOCTOR)
        # --------------------------------------------------

        pending_cases = db_select(
            table="skin_cases",
            filters={
                "status": CASE_PROCESSING
            }
        )

        for case in pending_cases:
            updated_at = datetime.datetime.fromisoformat(case["updated_at"])
            age_hours = (now - updated_at).total_seconds() / 3600

            if age_hours >= REVIEW_REMINDER_HOURS and case.get("assigned_doctor"):
                db_insert(
                    table="notifications",
                    payload={
                        "user_id": case["assigned_doctor"],
                        "title": "Pending Case Review",
                        "message": (
                            "You have a skin case pending review "
                            f"for over {REVIEW_REMINDER_HOURS} hours."
                        ),
                        "type": NOTIFY_CASE,
                        "action_url": f"/doctor/cases/{case['id']}"
                    }
                )

        # --------------------------------------------------
        # CRON HEALTH SUCCESS
        # --------------------------------------------------

        db_insert(
            table="cron_health",
            payload={
                "job_name": "send_reminders",
                "status": "success",
                "ran_at": job_started_at
            }
        )

        logger.info("Reminder job completed successfully")

    except Exception as e:
        logger.critical(f"Reminder job failed: {e}")

        db_insert(
            table="cron_health",
            payload={
                "job_name": "send_reminders",
                "status": "failed",
                "error": str(e),
                "ran_at": job_started_at
            }
        )
