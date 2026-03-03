from fastapi import APIRouter, Depends, status
from ..schemas.user import UserCreate, UserResponse 
from sqlalchemy.orm import Session
from ..db import get_db, User
from fastapi.exceptions import HTTPException



router = APIRouter(
    prefix="/users", 
    tags=["users"]
)

# endpoint for creating the user
@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)): 
    # construct a new user
    new_user = User(
        name=user.name, 
        email=user.email, 
        phone=user.phone
    )
    # add to database 
    try: 
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback() 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"failed to create user {e}"
        )
        
        
# fetch all users
@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)): 
    
    return db.query(User).all()

@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: str, db: Session = Depends(get_db)): 
    
    try: 
        user = db.query(User).filter(
            User.user_id == user_id
        ).first()
        if not user: 
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"user with id: {user_id} not found"
            )
        return user 
    except Exception as e: 
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"could'nt fetche user due to error {e}"
        )
    
