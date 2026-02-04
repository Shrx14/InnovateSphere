import time
import jwt
import logging
from backend.config import Config

logger = logging.getLogger(__name__)


def create_access_token(user_id: int, role: str = "user", username: str = "", email: str = "") -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "username": username,
        "email": email,
        "exp": int(time.time()) + Config.JWT_EXP_SECONDS,
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGO)
