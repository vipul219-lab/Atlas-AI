from fastapi import HTTPException

from app.database import get_session_user


def get_current_user(token: str):
    token = token.replace("Bearer ", "", 1).strip()
    user = get_session_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def require_admin(user: dict):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
