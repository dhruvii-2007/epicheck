# app/routers/tickets.py

from fastapi import APIRouter, HTTPException
from uuid import UUID
from datetime import datetime, timezone
from typing import Optional

from app.supabase_client import db_select, db_insert, db_update
from app.config import VALID_TICKET_STATUSES

router = APIRouter()

# --------------------------------------------------
# CREATE TICKET
# --------------------------------------------------

@router.post("/")
def create_ticket(
    user_id: UUID,
    subject: str,
    message: str,
):
    ticket = db_insert(
        table="tickets",
        payload={
            "user_id": str(user_id),
            "subject": subject,
            "message": message,
            "status": "open",
            "created_at": datetime.now(timezone.utc),
        }
    )

    db_insert(
        table="ticket_messages",
        payload={
            "ticket_id": ticket["id"],
            "sender_id": str(user_id),
            "message": message,
            "created_at": datetime.now(timezone.utc),
        }
    )

    return ticket

# --------------------------------------------------
# GET TICKET WITH MESSAGES
# --------------------------------------------------

@router.get("/{ticket_id}")
def get_ticket(ticket_id: UUID):
    ticket = db_select(
        table="tickets",
        filters={"id": str(ticket_id)},
        single=True
    )

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    messages = db_select(
        table="ticket_messages",
        filters={"ticket_id": str(ticket_id)},
    )

    ticket["messages"] = messages
    return ticket

# --------------------------------------------------
# ADD MESSAGE
# --------------------------------------------------

@router.post("/{ticket_id}/messages")
def add_message(
    ticket_id: UUID,
    sender_id: UUID,
    message: str,
):
    return db_insert(
        table="ticket_messages",
        payload={
            "ticket_id": str(ticket_id),
            "sender_id": str(sender_id),
            "message": message,
            "created_at": datetime.now(timezone.utc),
        }
    )

# --------------------------------------------------
# UPDATE TICKET STATUS
# --------------------------------------------------

@router.patch("/{ticket_id}/status")
def update_ticket_status(
    ticket_id: UUID,
    status: str,
):
    if status not in VALID_TICKET_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status")

    updated = db_update(
        table="tickets",
        filters={"id": str(ticket_id)},
        payload={"status": status}
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return updated[0]
