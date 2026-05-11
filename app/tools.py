from langchain_core.tools import tool
from .db import SessionLocal, Order, User


@tool 
def get_order_status(order_id: str) -> dict: 
    """
    Get the status and details of a SPECIFIC order.
    Use this ONLY when the user provides an explicit order ID.
    Parameter: order_id — the exact UUID of the order to look up.
    """
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
    """
    Get the 5 most recent orders for a user.
    Use this when the user asks about their orders WITHOUT providing a specific order ID.
    Parameter: user_id — the UUID of the user whose orders to retrieve.
    """
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


@tool
def cancel_order(order_id: str) -> dict:
    """
    Cancels an order if it is still in PENDING status.
    Parameter: order_id — the UUID of the order to cancel.
    Returns: A confirmation message or an error if the order cannot be cancelled.
    """
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            return {"error": "Order not found."}
        
        from .db import OrderStatus
        if order.status != OrderStatus.PENDING:
            return {"error": f"Cannot cancel order in {order.status.value} status. Only PENDING orders can be cancelled."}
        
        order.status = OrderStatus.CANCELLED
        db.commit()
        return {"success": True, "message": f"Order {order_id} has been cancelled successfully."}
    finally:
        db.close()


@tool
def initiate_return(order_id: str, reason: str) -> dict:
    """
    Initiates a return for a DELIVERED order.
    Parameter: order_id — the UUID of the order to return.
    Parameter: reason — the reason for the return.
    Returns: A confirmation message or an error if the return cannot be initiated.
    """
    # Simple implementation: in a real app, this would create a Return record
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            return {"error": "Order not found."}
        
        from .db import OrderStatus
        if order.status != OrderStatus.DELIVERED:
            return {"error": f"Cannot return an order that is {order.status.value}. Only DELIVERED orders can be returned."}
        
        # In a real system, we'd create a Return object here
        # For now, we'll just return a success message
        return {
            "success": True, 
            "message": f"Return initiated for order {order_id}. Reason: {reason}. A return label has been sent to your email."
        }
    finally:
        db.close()