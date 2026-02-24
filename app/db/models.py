from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy import ForeignKey, Column
from sqlalchemy import Enum, func
import enum, uuid 

def generate_unique_id(): 
    return uuid.uuid4()

class MessageRole(str, enum.Enum): 
    USER = "user"
    ASSISTANT = "assistant"
    
class OrderStatus(str, enum.Enum): 
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    
class TicketStatus(str, enum.Enum): 
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

    

class Base(DeclarativeBase): 
    pass 

# making the data models 
class User(Base): 
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, default=generate_unique_id)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False, unique=True)
    phone = Column(String(15), nullable=False, unique=False)

class Order(Base): 
    __tablename__ = "orders"

    order_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), nullable=False)
    total_amount = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    user_id = Column(String, ForeignKey("users.user_id", ondelete="CASCADE"))
    
class Message(Base): 
    __tablename__ = "messages"
    
    message_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    
    session_id = Column(String, ForeignKey(column="sessions.session_id", ondelete="CASCADE"))
    
    
class EscalationTicket(Base): 
    __tablename__ = "escalation_tickets"

    ticket_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reason = Column(String(100), nullable=False)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user_id = Column(String, ForeignKey(column="users.user_id", ondelete="CASCADE"))
    order_id = Column(String, ForeignKey(column="orders.order_id", ondelete="CASCADE"), nullable=True)
    session_id = Column(String, ForeignKey(column="sessions.session_id"))
    
class Session(Base): 
    __tablename__ = "sessions"

    session_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    is_active = Column(Boolean)

    user_id = Column(String, ForeignKey(column="users.user_id"))

    

    
