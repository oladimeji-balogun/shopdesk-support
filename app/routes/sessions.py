from fastapi import APIRouter, Depends, HTTPException
from ..db import get_db, Session as SessionModel 
from ..schemas import SessionCreate, SessionResponse 
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import UUID


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

@router.patch("/{session_id}/end", response_model=SessionResponse)
def end_session(session_id: str, db: DBSession = Depends(get_db)): 
    session = db.query(SessionModel).filter(
        SessionModel.session_id == session_id
    ).first()
    
    if not session: 
        raise HTTPException(status_code=404, detail=f"session with {session_id} not found")
    session.is_active = False 
    db.commit()
    db.refresh(session)
    return session