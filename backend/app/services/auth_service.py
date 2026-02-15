from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.repositories.user_repository import UserRepository
from app.dtos.auth_dto import TokenResponseDTO, SignupRequestDTO
from app.dtos.user_dto import UserCreateDTO
from app.utils.jwt_utils import create_access_token
from app.dtos.user_dto import UserCreateDTO, UserResponseDTO
from app.repositories.user_repository import UserRepository
from app.models.user import User  # <--- CRITICAL IMPORT: You need this to create the object

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Service for authentication operations."""

    def __init__(self, user_repository: UserRepository, user_service=None):
        self.user_repository = user_repository
        self.user_service = user_service

    def authenticate_user(self, username: str, password: str) -> TokenResponseDTO:
        user = self.user_repository.get_by_username(username)

        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if user is None:
            raise credentials_exception

        # Verify password using bcrypt
        if not pwd_context.verify(password, user.password):
            raise credentials_exception

        access_token = create_access_token(data={"sub": str(user.id)})
        return TokenResponseDTO(access_token=access_token, token_type="bearer")

    def signup_user(self, signup_dto: SignupRequestDTO) -> TokenResponseDTO:
        """
        Register a new user and generate a JWT token.

        Args:
            signup_dto: User signup information (username, password, name, preferences)

        Returns:
            TokenResponseDTO with JWT access token

        Raises:
            HTTPException: 400 if username already exists
        """
        if self.user_service is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="UserService not configured"
            )

        # Create user via UserService (handles password hashing and validation)
        user_create_dto = UserCreateDTO(
            username=signup_dto.username,
            password=signup_dto.password,
            name=signup_dto.name,
            preferences=signup_dto.preferences
        )

        created_user = self.user_service.create_user(user_create_dto)

        # Create JWT token for the new user
        access_token = create_access_token(data={"sub": str(created_user.id)})

        return TokenResponseDTO(access_token=access_token, token_type="bearer")
