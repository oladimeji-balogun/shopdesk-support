from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from ..db import get_db, Order, User
from ..auth.dependencies import get_current_user
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional

router = APIRouter(prefix="/orders", tags=["orders"])


class OrderRecord(BaseModel):
    order_id: UUID
    status: str
    total_amount: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


@router.get("/me", response_model=list[OrderRecord])
def get_my_orders(
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    orders = db.query(Order).filter(
        Order.user_id == current_user.user_id
    ).order_by(desc(Order.created_at)).all()
    return orders
