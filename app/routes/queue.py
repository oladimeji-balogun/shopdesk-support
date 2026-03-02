from fastapi import APIRouter, Depends
from ..schemas import TicketRecord 
from ..db import EscalationTicket, get_db, Session as SessionModel, User
from sqlalchemy.orm import Session as DBSession

router = APIRouter(
    prefix="/queue", 
    tags=["queue"]
)

@router.get("/")
def submit_escalation_ticket(
    session_id: str, 
    ticket_record: TicketRecord,
    db: DBSession = Depends(get_db)
): 
    
    user = db.query(SessionModel).filter(
        SessionModel.session_id == session_id
    ).first()
    
    new_ticket = EscalationTicket(
        reason=ticket_record.reason, 
        user_id=user.user_id, 
        session_id=session_id, 
        status=ticket_record.status
    )
    
    db.add(new_ticket)
    db.commit()
    return {
        "message": "successfully submitted the escalation ticket"
    }