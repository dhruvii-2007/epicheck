from fastapi import APIRouter
from app.supabase_client import db_select, db_insert

router = APIRouter()

@router.get("/")
def list_tickets():
    return db_select("tickets")

@router.post("/")
def create_ticket(payload: dict):
    return db_insert("tickets", payload)
create_notification( user_id=ticket["user_id"], title="Support replied", message="You received a reply on your support ticket.", notif_type="ticket_reply", action_url=f"/tickets/{ticket_id}" )
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.core.dependencies import get_current_user
from app.core.roles import require_support_or_admin
from app.supabase_client import supabase
from app.services.notifications import create_notification

router = APIRouter(prefix="/tickets", tags=["Support & Tickets"])


# --------------------------------------------------
# CREATE TICKET
# --------------------------------------------------
@router.post("")
def create_ticket(payload: dict, profile=Depends(get_current_user)):
    """
    User creates a support ticket
    """
    subject = payload.get("subject")
    message = payload.get("message")

    if not subject or not message:
        raise HTTPException(status_code=400, detail="subject and message required")

    ticket_resp = supabase.table("tickets").insert({
        "user_id": profile["id"],
        "subject": subject,
        "message": message,
        "status": "open",
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    if not ticket_resp.data:
        raise HTTPException(status_code=500, detail="Ticket creation failed")

    return ticket_resp.data[0]


# --------------------------------------------------
# LIST TICKETS
# --------------------------------------------------
@router.get("")
def list_tickets(profile=Depends(get_current_user)):
    """
    User: own tickets
    Support/Admin: all tickets
    """

    query = supabase.table("tickets").select("*").is_("deleted_at", None)

    if profile["role"] not in ["support", "admin"]:
        query = query.eq("user_id", profile["id"])

    resp = query.order("created_at", desc=True).execute()
    return resp.data or []


# --------------------------------------------------
# GET TICKET DETAILS
# --------------------------------------------------
@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, profile=Depends(get_current_user)):
    """
    Get ticket + messages
    """

    ticket_query = (
        supabase
        .table("tickets")
        .select("*")
        .eq("id", ticket_id)
        .is_("deleted_at", None)
    )

    if profile["role"] not in ["support", "admin"]:
        ticket_query = ticket_query.eq("user_id", profile["id"])

    ticket_resp = ticket_query.limit(1).execute()

    if not ticket_resp.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = ticket_resp.data[0]

    messages = (
        supabase
        .table("ticket_messages")
        .select("*")
        .eq("ticket_id", ticket_id)
        .is_("deleted_at", None)
        .order("created_at")
        .execute()
    ).data or []

    return {
        "ticket": ticket,
        "messages": messages
    }


# --------------------------------------------------
# ADD MESSAGE TO TICKET
# --------------------------------------------------
@router.post("/{ticket_id}/message")
def add_ticket_message(
    ticket_id: str,
    payload: dict,
    profile=Depends(get_current_user)
):
    """
    Add a message to a ticket
    """

    message = payload.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="message required")

    # verify ticket access
    ticket_query = supabase.table("tickets").select("*").eq("id", ticket_id)

    if profile["role"] not in ["support", "admin"]:
        ticket_query = ticket_query.eq("user_id", profile["id"])

    ticket_resp = ticket_query.limit(1).execute()

    if not ticket_resp.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = ticket_resp.data[0]

    # insert message
    supabase.table("ticket_messages").insert({
        "ticket_id": ticket_id,
        "sender_id": profile["id"],
        "message": message,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    # notify user if support/admin replied
    if profile["role"] in ["support", "admin"]:
        create_notification(
            user_id=ticket["user_id"],
            title="Support replied",
            message="You received a reply on your support ticket.",
            notif_type="ticket_reply",
            action_url=f"/tickets/{ticket_id}"
        )

    return {"status": "message_sent"}


# --------------------------------------------------
# UPDATE TICKET STATUS
# --------------------------------------------------
@router.put("/{ticket_id}/status")
def update_ticket_status(
    ticket_id: str,
    payload: dict,
    support=Depends(require_support_or_admin)
):
    """
    Update ticket status
    """

    new_status = payload.get("status")
    allowed = ["open", "in_progress", "resolved", "closed"]

    if new_status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid status")

    resp = (
        supabase
        .table("tickets")
        .update({
            "status": new_status,
            "updated_at": datetime.utcnow().isoformat()
        })
        .eq("id", ticket_id)
        .execute()
    )

    if not resp.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {"status": "updated"}
