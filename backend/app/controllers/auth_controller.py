from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.dtos.auth_dto import LoginRequestDTO, TokenResponseDTO

router = APIRouter(tags=["authentication"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to create AuthService instance."""
    user_repository = UserRepository(db)
    return AuthService(user_repository)


@router.post("/login", response_model=TokenResponseDTO)
def login(
    login_dto: LoginRequestDTO,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user and return JWT access token.

    Args:
        login_dto: Login credentials (username and password)
        auth_service: Injected authentication service

    Returns:
        TokenResponseDTO with JWT access token

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    return auth_service.authenticate_user(login_dto.username, login_dto.password)


@router.post("/logout")
def logout():
    """
    Logout endpoint (client-side only).

    Since JWT is stateless, this endpoint simply returns a success message.
    The client is responsible for deleting the token from storage.

    Returns:
        Success message
    """
    return {"message": "Successfully logged out"}
