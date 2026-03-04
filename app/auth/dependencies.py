from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from .jwt import decode_token 
from ..db import User, get_db
from sqlalchemy.orm import Session
from jose import JWTError



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)): 
    try:
        user_data = decode_token(token=token)
    except JWTError: 
        raise HTTPException(
            status_code=401, 
            detail="invalid user credentials"
        )
        
    if user_data.get("type") == "refresh": 
        raise HTTPException(
            status_code=401, 
            detail="incorrect token type"
        )
    # verifying the user signature on the database 
    user = db.query(User).filter(
        User.user_id == user_data["user_id"]
    ).first()

    if user is None: 
        raise HTTPException(status_code=404, detail="user not found")
    return user
    
    