from fastapi import FastAPI, Depends
from app.routes import chat, queue, sessions, user, auth
from app.db import get_db, test_db_connection
from sqlalchemy.orm import Session
from sqlalchemy import text

# fastapi app 
app = FastAPI()
app.include_router(router=chat.router)
app.include_router(router=queue.router)
app.include_router(router=sessions.router)
app.include_router(router=user.router)
app.include_router(router=auth.router)


@app.get("/health")
async def get_health(db: Session = Depends(get_db)): 
    try: 
        db.execute(text("SELECT 1"))
        return {"status": "healty", "db": "connected"}
    except Exception as e: 
        return {"status": "unhealthy", "db": "disconnected"}