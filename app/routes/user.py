from fastapi import APIRouter, Depends, status, Request
from ..schemas.user import UserCreate, UserResponse 
from sqlalchemy.orm import Session
from ..db import get_db, User
from fastapi.exceptions import HTTPException
from ..auth.dependencies import get_current_user
from ..auth.password import hash_password
from ..db.models import UserRole
from pydantic import BaseModel
from typing import Optional

router = APIRouter(
    prefix="/users", 
    tags=["users"]
)


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admins only")
    return current_user


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if payload.name:
        current_user.name = payload.name
    if payload.phone:
        current_user.phone = payload.phone
    db.commit()
    db.refresh(current_user)
    return current_user


# ── Admin endpoints ───────────────────────────────────────────────────────────

class RoleUpdate(BaseModel):
    role: UserRole


@router.get("/", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin)
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: str,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin)
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin)
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin)
):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user

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
    
