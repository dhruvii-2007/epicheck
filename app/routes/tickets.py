from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from ..auth import (
    require_user,
    require_admin
)
from ..supabase_client import (
    db_select,
    db_insert,
    db_update
)
from ..config import (
    TICKET_OPEN,
    TICKET_IN_PROGRESS,
    TICKET_CLOSED
)

router = APIRouter(
    prefix="/v1/tickets",
    tags=["Support Tickets"]
)

# --------------------------------------------------
# CREATE TICKET (USER)
# --------------------------------------------------
@router.post("/")
def create_ticket(
    subject: str,
    message: str,
    user=Depends(require_user)
):
    ticket = db_insert(
        table="tickets",
        payload={
            "user_id": user["sub"],
            "subject": subject,
            "status": TICKET_OPEN,
            "created_at": datetime.utcnow().isoformat()
        }
    )

    db_insert(
        table="ticket_messages",
        payload={
            "ticket_id": ticket["id"],
            "sender_id": user["sub"],
            "message": message,
            "created_at": datetime.utcnow().isoformat()
        }
    )

    return {"ticket_id": ticket["id"]}

# --------------------------------------------------
# GET MY TICKETS (USER)
# --------------------------------------------------
@router.get("/")
def get_my_tickets(
    user=Depends(require_user)
):
    tickets = db_select(
        table="tickets",
        filters={
            "user_id": user["sub"],
            "deleted_at": None
        }
    )

    return {"tickets": tickets}

# --------------------------------------------------
# GET TICKET DETAILS
# --------------------------------------------------
@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: str,
    user=Depends(require_user)
):
    ticket = db_select(
        table="tickets",
        filters={
            "id": ticket_id,
            "deleted_at": None
        },
        single=True
    )

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if user["role"] not in ["admin", "support"] and ticket["user_id"] != user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")

    messages = db_select(
        table="ticket_messages",
        filters={
            "ticket_id": ticket_id,
            "deleted_at": None
        }
    )

    return {
        "ticket": ticket,
        "messages": messages
    }

# --------------------------------------------------
# ADD MESSAGE TO TICKET
# --------------------------------------------------
@router.post("/{ticket_id}/reply")
def reply_ticket(
    ticket_id: str,
    message: str,
    user=Depends(require_user)
):
    ticket = db_select(
        table="tickets",
        filters={"id": ticket_id},
        single=True
    )

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if user["role"] not in ["admin", "support"] and ticket["user_id"] != user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    db_insert(
        table="ticket_messages",
        payload={
            "ticket_id": ticket_id,
            "sender_id": user["sub"],
            "message": message,
            "created_at": datetime.utcnow().isoformat()
        }
    )

    if ticket["status"] == TICKET_OPEN:
        db_update(
            table="tickets",
            payload={
                "status": TICKET_IN_PROGRESS,
                "updated_at": datetime.utcnow().isoformat()
            },
            filters={"id": ticket_id}
        )

    return {"sent": True}

# --------------------------------------------------
# ASSIGN TICKET (ADMIN)
# --------------------------------------------------
@router.post("/{ticket_id}/assign/{staff_id}")
def assign_ticket(
    ticket_id: str,
    staff_id: str,
    admin=Depends(require_admin)
):
    db_update(
        table="tickets",
        payload={
            "assigned_to": staff_id,
            "status": TICKET_IN_PROGRESS,
            "updated_at": datetime.utcnow().isoformat()
        },
        filters={"id": ticket_id}
    )

    return {"assigned": True}

# --------------------------------------------------
# CLOSE TICKET
# --------------------------------------------------
@router.post("/{ticket_id}/close")
def close_ticket(
    ticket_id: str,
    user=Depends(require_user)
):
    ticket = db_select(
        table="tickets",
        filters={"id": ticket_id},
        single=True
    )

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if user["role"] not in ["admin", "support"] and ticket["user_id"] != user["sub"]:
        raise HTTPException(status_code=403, detail="Forbidden")

    db_update(
        table="tickets",
        payload={
            "status": TICKET_CLOSED,
            "updated_at": datetime.utcnow().isoformat()
        },
        filters={"id": ticket_id}
    )

    return {"closed": True}
