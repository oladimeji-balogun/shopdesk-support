from ..auth.dependencies import get_current_user
from ..db import get_db, User
from sqlalchemy.orm import Session as DBSession 
from fastapi import APIRouter, Depends, HTTPException, status, Request
from ..schemas import UserOut, UserCreate, UserLogin, TokenResponse, Token
from ..auth.password import hash_password, verify_password
from ..auth.jwt import create_access_token, create_refresh_token, decode_token
from jose import JWTError
from ..limiter import limiter
from ..utils.rate_limiting import get_user_id
router = APIRouter(
    prefix="/auth", 
    tags=["auth"]
)

# enpoint to create a new users
@router.post("/register", response_model=TokenResponse)
@limiter.limit("10/min", key_func=get_user_id)
def create_user(request: Request, user_data: UserCreate, db: DBSession = Depends(get_db)): 
    # check whether a user with the same email already exist 
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()
    
    if existing_user is not None: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="user with same email alredy exist"
        )
    
    # creating the new user for the database 
    new_user = User(
        name=user_data.name, 
        email=user_data.email, 
        hashed_password=hash_password(password=user_data.password),
        phone=user_data.phone
    )
        
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # return a fresh token so user can be granted acces right away
    access_token = create_access_token(data={
        "user_id": str(new_user.user_id)
    })
    
    refresh_token = create_refresh_token(data={
        "user_id": str(new_user.user_id)
    })
    return {
        "refresh_token": refresh_token, 
        "access_token": access_token, 
        "user_id": str(new_user.user_id),
        "type": "bearer", 
        "role": new_user.role
    }
    
    
@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute", key_func=get_user_id)
def login_user(request: Request, user_data: UserLogin, db: DBSession = Depends(get_db)): 
    # check if usre exist 
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if user is None: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="no account found with theese loging details"
        )
        
    # veify if password is correct 
    if not verify_password(hashed_password=user.hashed_password, plain_password=user_data.password): 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="incorrect password"
        )
        
    # create new tokens for the user 
    access_token = create_access_token(data={
        "user_id": str(user.user_id)
    })
    refresh_token = create_refresh_token(data={
        "user_id": str(user.user_id)
    })
    
    return {
        "refresh_token": refresh_token, 
        "user_id": str(user.user_id),
        "access_token": access_token, 
        "type": "bearer"
    }
    
# endpoint to refresh tokens 
@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute", key_func=get_user_id)
def refresh_tokens(request: Request, token: Token): 
    try: 
        data = decode_token(token=token.content)
    except JWTError: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="invalid or expired token"
        )
    
    # verify the token type
    if data["type"] != "refresh": 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="invalid token type"
        )
        
    access_token = create_access_token(data={
        "user_id": data["user_id"]
    })
    refresh_token = create_refresh_token(data={
        "user_id": data["user_id"]
    })
    
    return {
        "refresh_token": refresh_token, 
        "access_token": access_token, 
        "type": "bearer"
    }
    
@router.post("/logout")
@limiter.limit("10/minute", key_func=get_user_id)
def logout_user(request: Request): 
    return {"message": "success"}