from app.db import SessionLocal 
from app.tools import get_order_status, get_recent_orders, get_account_info
import pytest 

def test_get_order_status(): 
    order = get_order_status(order_id="0705cc38-5650-4e7c-afa2-60c2bfca06a6")
    assert isinstance(order, dict)
    assert len(order.keys()) == 4
    
def test_get_recent_orders(): 
    orders = get_recent_orders(user_id="066684c6-d722-4353-8a01-a21dda9bb5f2")
    assert isinstance(orders, list[dict])
    assert len(orders) == 5 
    
def tes_get_account_info(): 
    user = get_account_info(user_id="066684c6-d722-4353-8a01-a21dda9bb5f2")
    assert isinstance(user, dict)
