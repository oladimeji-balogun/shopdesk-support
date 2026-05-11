from fastapi import APIRouter, Depends, Request, HTTPException, Query
from ..schemas import TicketRecord, TicketUpdate
from ..db import EscalationTicket, get_db, TicketStatus, User, Message, MessageRole
from sqlalchemy.orm import Session as DBSession
from ..auth.dependencies import get_current_user
from ..db.models import UserRole
from typing import Optional
from pydantic import BaseModel, Field

from ..limiter import limiter
from ..utils.rate_limiting import get_user_id

router = APIRouter(
    prefix="/queue", 
    tags=["queue"]
)

@router.get("/", response_model=list[TicketRecord])
@limiter.limit("30/minute", key_func=get_user_id)
def get_tickets(
    request: Request,
    status: Optional[str] = Query(default=None),
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
): 
    query = db.query(EscalationTicket)
    if status:
        try:
            ticket_status = TicketStatus(status)
            query = query.filter(EscalationTicket.status == ticket_status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"invalid status: {status}")
    else:
        query = query.filter(EscalationTicket.status == TicketStatus.OPEN)

    return query.order_by(EscalationTicket.created_at.desc()).all()


@router.patch("/{ticket_id}")
def update_ticket(
    ticket_id: str, 
    update: TicketUpdate,
    db: DBSession = Depends(get_db), 
    user: User = Depends(get_current_user)
): 
    ticket = db.query(EscalationTicket).filter(
        EscalationTicket.ticket_id == ticket_id
    ).first()

    if not ticket: 
        raise HTTPException(status_code=404, detail="no tickets found")
        
    ticket.status = update.status
    db.commit()
    db.refresh(ticket)
    return {"message": "successful"}


class AgentReply(BaseModel):
    content: str = Field(..., min_length=1, max_length=4096)


@router.post("/{ticket_id}/reply")
def reply_to_ticket(
    ticket_id: str,
    payload: AgentReply,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Agent sends a direct reply into the customer's session."""
    if current_user.role not in (UserRole.AGENT, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="agents only")

    ticket = db.query(EscalationTicket).filter(
        EscalationTicket.ticket_id == ticket_id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")

    message = Message(
        session_id=ticket.session_id,
        role=MessageRole.ASSISTANT,
        content=payload.content
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return {
        "message_id": str(message.message_id),
        "content": message.content,
        "role": message.role,
        "created_at": message.created_at
    }


class AssignPayload(BaseModel):
    agent_id: str


@router.patch("/{ticket_id}/assign")
def assign_ticket(
    ticket_id: str,
    payload: AssignPayload,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in (UserRole.AGENT, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="agents only")

    ticket = db.query(EscalationTicket).filter(
        EscalationTicket.ticket_id == ticket_id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")

    # verify the target agent exists
    agent = db.query(User).filter(User.user_id == payload.agent_id).first()
    if not agent or agent.role not in (UserRole.AGENT, UserRole.ADMIN):
        raise HTTPException(status_code=400, detail="invalid agent")

    ticket.assigned_to = agent.user_id
    db.commit()
    db.refresh(ticket)
    return {"message": "ticket assigned", "assigned_to": str(ticket.assigned_to)}
    