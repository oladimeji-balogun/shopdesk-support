from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import Integer, String, DateTime, Boolean, Float
from sqlalchemy import ForeignKey, Column


# making the data models 
class User(DeclarativeBase): 
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    phone = Column(String(15), nullable=False, unique=False)

class Order(DeclarativeBase): 
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True)
    status = Column(Boolean, nullable=False)
    total_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

