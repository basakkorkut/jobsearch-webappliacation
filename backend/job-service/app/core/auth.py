import logging

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import settings

logger = logging.getLogger(__name__)

_bearer = HTTPBearer()
_bearer_optional = HTTPBearer(auto_error=False)


class CurrentUser:
    def __init__(self, id: str, email: str | None = None) -> None:
        self.id = id
        self.email = email


def _decode_token(token: str) -> dict:
    try:
        if settings.supabase_jwt_secret:
            return pyjwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        # Development fallback — no signature check
        logger.warning("SUPABASE_JWT_SECRET not set — skipping signature verification")
        return pyjwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=["HS256"],
        )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except pyjwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}")


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> CurrentUser:
    payload = _decode_token(credentials.credentials)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing sub claim")
    return CurrentUser(id=user_id, email=payload.get("email"))


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
) -> CurrentUser | None:
    if credentials is None:
        return None
    payload = _decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        return None
    return CurrentUser(id=user_id, email=payload.get("email"))
