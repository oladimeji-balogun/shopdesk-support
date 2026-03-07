from fastapi import FastAPI, Depends
from app.routes import chat, queue, sessions, user, auth
from app.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

# imports for rate limiting
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app import limiter


# fastapi app 
app = FastAPI(title="ShopDesk Customer Support API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(router=chat.router)
app.include_router(router=queue.router)
app.include_router(router=sessions.router)
app.include_router(router=user.router)
app.include_router(router=auth.router)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

@app.get("/health")
async def get_health(db: Session = Depends(get_db)): 
    try: 
        db.execute(text("SELECT 1"))
        return {"status": "healty", "db": "connected"}
    except Exception as e: 
        return {"status": "unhealthy", "db": "disconnected"}