from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.repositories.user_repository import UserRepository
from app.dtos.auth_dto import TokenResponseDTO
from app.utils.jwt_utils import create_access_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication operations."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def authenticate_user(self, username: str, password: str) -> TokenResponseDTO:
        """
        Authenticate a user and generate a JWT token.

        Args:
            username: Username for authentication
            password: Plain text password

        Returns:
            TokenResponseDTO with JWT access token

        Raises:
            HTTPException: 401 if credentials are invalid
        """
        # Get user from database
        user = self.user_repository.get_by_username(username)

        # Use same error message for both cases to prevent username enumeration
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if user is None:
            raise credentials_exception

        # Verify password
        if not pwd_context.verify(password, user.password):
            raise credentials_exception

        # Create JWT token with user ID as subject
        access_token = create_access_token(data={"sub": str(user.id)})

        return TokenResponseDTO(access_token=access_token, token_type="bearer")
