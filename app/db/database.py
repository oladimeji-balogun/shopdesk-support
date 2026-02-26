from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker, Session 

from ..config import config
from ..utils.logger import setup_logger 

logger = setup_logger(
    name="database", 
    filepath="./logs/database.log", 
    verbose=True
)

logger.info(msg="connecting to database")
engine = create_engine(url=config.DATABASE_URI)
logger.info("connected to database successfully")
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