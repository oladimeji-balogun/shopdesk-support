from jose import jwt, JWTError
from datetime import time, timedelta, timezone, datetime 
from ..config import config 


def create_access_token(data: dict) -> str: 
    data = data.copy()
    exp = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)

    data.update({
        "exp": exp, 
        "type": "access" 
    })
    
    return jwt.encode(
        claims=data, 
        key=config.JWT_SECRET_KEY, 
        algorithm=[config.JWT_ALGORITHM]
    )
    
def create_refresh_token(data: dict) -> str: 
    data = data.copy()

    exp = datetime.now(timezone.utc) + timedelta(hours=config.REFRESH_TOKEN_EXPIRE_HOURS)
    data.update({
        "exp": exp, 
        "type": "refresh"
    })
    
    return jwt.encode(
        claims=data, 
        key=config.JWT_SECRET_KEY, 
        algorithm=[config.JWT_ALGORITHM]
    )
    
def decode_token(token: str) -> dict: 
    try: 
        data = jwt.decode(
            token=token, 
            key=config.JWT_SECRET_KEY, 
            algorithms=[config.JWT_ALGORITHM]
        )
    except JWTError: 
        raise JWTError("invalid access token") 
    
    return data 