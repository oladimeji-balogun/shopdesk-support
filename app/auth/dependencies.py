from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from .jwt import decode_token
from ..db import User, get_db
from sqlalchemy.orm import Session
from jose import JWTError

# In-memory token blacklist (JTIs of revoked tokens).
# In production, replace with a Redis set using the token's TTL.
_revoked_jtis: set[str] = set()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def revoke_token(jti: str) -> None:
    """Add a token's JTI to the blacklist."""
    _revoked_jtis.add(jti)


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

    # Check token blacklist (loggedout tokens)
    jti = user_data.get("jti")
    if jti and jti in _revoked_jtis:
        raise HTTPException(
            status_code=401,
            detail="token has been revoked"
        )

    # Verify the user exists in the database
    user = db.query(User).filter(
        User.user_id == user_data["user_id"]
    ).first()

    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return user