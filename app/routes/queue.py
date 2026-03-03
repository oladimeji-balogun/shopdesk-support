from fastapi import APIRouter, Depends
from ..schemas import TicketRecord 
from ..db import EscalationTicket, get_db, TicketStatus
from sqlalchemy.orm import Session as DBSession

router = APIRouter(
    prefix="/queue", 
    tags=["queue"]
)

@router.get("/", response_model=list[TicketRecord])
def get_open_tickets(
    db: DBSession = Depends(get_db)
): 
    
    open_tickets = db.query(EscalationTicket).filter(
        EscalationTicket.status == TicketStatus.OPEN
    ).all()
    return open_tickets