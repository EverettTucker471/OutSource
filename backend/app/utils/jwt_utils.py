from datetime import datetime, timedelta
from typing import Dict
from jose import JWTError, jwt
from app.config import settings


def create_access_token(data: Dict[str, str]) -> str:
    """
    Create a JWT access token with expiration.

    Args:
        data: Dictionary containing the token payload (typically {"sub": user_id})

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Dict[str, str]:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token string to verify

    Returns:
        Decoded token payload dictionary

    Raises:
        JWTError: If token is invalid or malformed
        ExpiredSignatureError: If token has expired
    """
    payload = jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    return payload
