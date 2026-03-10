from fastapi import APIRouter, Depends, Request, HTTPException
from ..schemas import TicketRecord, TicketUpdate
from ..db import EscalationTicket, get_db, TicketStatus, User
from sqlalchemy.orm import Session as DBSession
from ..auth.dependencies import get_current_user

from ..limiter import limiter
from ..utils.rate_limiting import get_user_id

router = APIRouter(
    prefix="/queue", 
    tags=["queue"]
)

@router.get("/", response_model=list[TicketRecord])
@limiter.limit("5/minute", key_func=get_user_id)
def get_open_tickets(
    request: Request,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
): 
    
    open_tickets = db.query(EscalationTicket).filter(
        EscalationTicket.status == TicketStatus.OPEN
    ).all()
    return open_tickets


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
        raise HTTPException(
            status_code=404, 
            detail="no tickets found"
        )
        
    ticket.status = update.status
    db.commit()
    db.refresh(ticket)

    return {"message": "successful"}
    