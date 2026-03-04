from passlib.context import CryptContext

password_context = CryptContext(schemes=["bcrypt"])

def hash_password(password: str) -> str: 
    return password_context.hash(
        secret=password    
    )
    
def verify_password(hashed_password: str, plain_password: str) -> bool: 
    return password_context.verify(
        secret=plain_password, 
        hash=hashed_password    
    )