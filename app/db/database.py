from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker, Session 

from ..config import config

engine = create_engine(url=config.DATABASE_URI)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db(): 
    db = SessionLocal()
    try: 
        yield db 
    finally: 
        db.close()
        
def test_db_connection(): 
    try: 
        with engine.connect() as conn: 
            print("database connection successful")
    except Exception as e: 
        print(f"failed to connect: {e}")
        
# test_db_connection()