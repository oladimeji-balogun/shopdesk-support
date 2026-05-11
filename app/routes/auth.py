from ..auth.dependencies import get_current_user, revoke_token
from ..db import get_db, User
from sqlalchemy.orm import Session as DBSession
from fastapi import APIRouter, Depends, HTTPException, status, Request
from ..schemas import UserOut, UserCreate, UserLogin, TokenResponse, Token
from ..auth.password import hash_password, verify_password
from ..auth.jwt import create_access_token, create_refresh_token, decode_token
from jose import JWTError
from ..limiter import limiter
from ..utils.rate_limiting import get_user_id
from pydantic import BaseModel, EmailStr

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


# endpoint to create a new user
@router.post("/register", response_model=TokenResponse)
@limiter.limit("10/min", key_func=get_user_id)
def create_user(request: Request, user_data: UserCreate, db: DBSession = Depends(get_db)):
    # check whether a user with the same email already exists
    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="an account with this email already exists"
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

    # return a fresh token so user can be granted access right away
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
    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    # Bug 2.6: Use generic error to prevent user enumeration
    if user is None or not verify_password(hashed_password=user.hashed_password, plain_password=user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid email or password"
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
        "type": "bearer",
        "role": user.role
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
def logout_user(request: Request, current_user=Depends(get_current_user), token: str = Depends(lambda req: req.headers.get("Authorization", "").replace("Bearer ", ""))):
    """
    Invalidates the current access token by adding its JTI to the blacklist.
    Future requests with this token will be rejected with 401.
    """
    try:
        from fastapi.security import OAuth2PasswordBearer
        from ..auth.jwt import decode_token as _decode
        # Extract token from Authorization header directly
        auth_header = request.headers.get("Authorization", "")
        raw_token = auth_header.replace("Bearer ", "")
        if raw_token:
            token_data = _decode(raw_token)
            jti = token_data.get("jti")
            if jti:
                revoke_token(jti)
    except Exception:
        pass  # Still return success even if blacklisting fails

    return {"message": "logged out successfully"}


# ── Password Reset ────────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
@limiter.limit("5/minute", key_func=get_user_id)
def forgot_password(request: Request, payload: ForgotPasswordRequest, db: DBSession = Depends(get_db)):
    """
    Initiates the password reset flow.
    In production: generate a signed token and email it to the user.
    Currently: returns the token in the response for development purposes.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    # Always return the same response to avoid user enumeration
    if not user:
        return {"message": "If that email exists, a reset link has been sent."}

    reset_token = create_access_token(data={"user_id": str(user.user_id), "purpose": "password_reset"})
    # TODO: send reset_token via email instead of returning it
    return {
        "message": "If that email exists, a reset link has been sent.",
        "dev_token": reset_token  # Remove in production
    }


@router.post("/reset-password")
@limiter.limit("5/minute", key_func=get_user_id)
def reset_password(request: Request, payload: ResetPasswordRequest, db: DBSession = Depends(get_db)):
    """Validates the reset token and updates the user's password."""
    try:
        token_data = decode_token(token=payload.token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid or expired reset token")

    if token_data.get("purpose") != "password_reset":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid token type")

    user = db.query(User).filter(User.user_id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()

    # Invalidate the reset token
    jti = token_data.get("jti")
    if jti:
        revoke_token(jti)

    return {"message": "password updated successfully"}