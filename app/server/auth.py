"""Fixed Bearer JWT per environment."""

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from server.config import settings
from util.logging import get_logger

logger = get_logger()
_bearer = HTTPBearer(auto_error=False)


def verify_access_token(token: str) -> None:
    if not settings.API_JWT_SECRET:
        logger.error("API_JWT_SECRET not configured")
        raise HTTPException(status_code=500, detail="Auth not configured")
    try:
        jwt.decode(
            token,
            settings.API_JWT_SECRET,
            algorithms=[settings.API_JWT_ALGORITHM],
        )
    except jwt.InvalidTokenError as err:
        logger.warning(f"JWT rejected: {err}")
        raise HTTPException(status_code=401, detail="Unauthorized") from err


async def require_jwt(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Unauthorized")
    verify_access_token(credentials.credentials)