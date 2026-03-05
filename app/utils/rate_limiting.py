from fastapi import Request
from ..auth.jwt import decode_token
from slowapi.util import get_remote_address

def get_user_id(request: Request) -> str:
    # extract user_id from jwt in the authorization header
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        data = decode_token(token)
        return data["user_id"]
    except Exception:
        return get_remote_address(request)  # fallback to ip if no token