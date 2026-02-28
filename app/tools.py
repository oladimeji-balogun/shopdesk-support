from langchain_core.tools import tool
from .db import SessionLocal, Order, User


@tool 
def get_order_status(order_id: str) -> dict: 
    """get the status and information about an order by its ID"""
    db = SessionLocal()
    try: 
        result = db.query(Order).filter(
            Order.order_id == order_id
        ).first()
        
        if result is None: 
            return {"error": "order not found"}
        return {
            "order_id": result.order_id, 
            "status": result.status.value, 
            "total_amount": result.total_amount, 
            "created_at": result.created_at 
        }
    finally: 
        db.close()
        
@tool 
def get_recent_orders(user_id: str) -> list[dict]: 
    """get the top five most recent orders by a user"""
    db = SessionLocal()
    try: 
        orders = db.query(Order).filter(
            Order.user_id == user_id
        ).order_by(
            Order.created_at.desc()
        ).limit(
            limit=5
        )
        
        if not orders: 
            return {"error": "no orders found"}
        return [
            {
                "order_date": order.created_at, 
                "total_amount": order.total_amount, 
                "status": order.status.value, 
                "created_at": order.created_at
            } for order in orders
        ]
    finally: 
        db.close()

@tool 
def get_account_info(user_id: str) -> dict: 
    """get the details of a user using his or her ID"""

    db = SessionLocal()
    try: 
        user = db.query(User).filter(
            User.user_id == user_id
        ).first()

        if not user: 
            return {"error": "no user found"}
        return {
            "user_email": user.email, 
            "name": user.name, 
            "phone": user.phone
        }
    finally: 
        db.close()