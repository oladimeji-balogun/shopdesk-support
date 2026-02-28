from faker import Faker
from uuid import uuid4
from .models import OrderStatus, User, Order, Base
from .database import SessionLocal, engine

from ..utils.logger import setup_logger 

logger = setup_logger(
    name="seed", 
    verbose=True
)
# create all the tables 

Base.metadata.create_all(bind=engine)
logger.info("database tables created successfully")
# the faker instance
fake = Faker()
    
def generate_fake_users(n: int) -> list[dict]: 
    fake_users = []

    for i in range(n): 
        fake_users.append({
            "user_id": fake.uuid4(), 
            "name": fake.name(), 
            "email": fake.email(), 
            "phone": fake.numerify(text="###-###-####")
        })
    return fake_users


def generate_order_for_users(n: int, users: list[dict]) -> list[dict]: 
    
    fake_orders = []
    user_ids = [user["user_id"] for user in users]
    statuses = [OrderStatus.PENDING, OrderStatus.CANCELLED, OrderStatus.DELIVERED, OrderStatus.SHIPPED]
    for i in range(n): 
        fake_orders.append({
            "order_id": fake.uuid4(), 
            "status": fake.random_element(elements=statuses), 
            "total_amount": round(fake.pyfloat(min_value=5, max_value=500, right_digits=2), 2), 
            "created_at": fake.date_time(), 
            "updated_at": fake.date_time(), 
            "user_id": fake.random_element(elements=user_ids)
        })

    return fake_orders


def seed(): 
    users = generate_fake_users(n=20)
    orders = generate_order_for_users(n=20, users=users)

    db = SessionLocal()
    try: 
        existing = db.query(User).first()

        if existing: 
            print("data already existing")
            return 
        db.add_all([User(**user_data) for user_data in users])
        db.flush()
        
        db.add_all([Order(**order_data) for order_data in orders])
        db.commit()
    finally: 
        db.close()

if __name__ == "__main__": 
    seed()