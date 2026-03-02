from fastapi import APIRouter, Depends
from ..db import get_db, Session as SessionModel 
from ..schemas import SessionCreate, SessionResponse 
from sqlalchemy.orm import Session as DBSession


router = APIRouter(
    prefix="/sessions", 
    tags=["sessions"]
)


# make the session creation route 
@router.post("/", response_model=SessionResponse)
def create_session(session: SessionCreate, db: DBSession = Depends(get_db)): 
    new_session = SessionModel(
        user_id=session.user_id
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session