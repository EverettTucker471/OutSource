from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.jwt_utils import verify_token

# OAuth2 scheme for extracting Bearer tokens from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Dependency that extracts and validates JWT token, then returns the authenticated user.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User model instance for the authenticated user

    Raises:
        HTTPException: 401 if token is invalid, expired, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode and verify the JWT token
        payload = verify_token(token)
        user_id_str: str = payload.get("sub")

        if user_id_str is None:
            raise credentials_exception

        # Convert user_id from string to integer
        try:
            user_id = int(user_id_str)
        except ValueError:
            raise credentials_exception

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception

    # Fetch user from database by ID
    user_repository = UserRepository(db)
    user = user_repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
