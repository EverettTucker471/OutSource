from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

# Make sure you import these DTOs!
from app.dtos.user_dto import UserCreateDTO, UserResponseDTO
from app.dtos.auth_dto import LoginRequestDTO, TokenResponseDTO
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.dtos.auth_dto import LoginRequestDTO, SignupRequestDTO, TokenResponseDTO

router = APIRouter(tags=["authentication"])

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    user_repository = UserRepository(db)
    user_service = UserService(user_repository)
    return AuthService(user_repository, user_service)

# Login looks good!
@router.post("/login", response_model=TokenResponseDTO)
def login(
    login_dto: LoginRequestDTO,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.authenticate_user(login_dto.username, login_dto.password)

@router.post("/signup", response_model=TokenResponseDTO, status_code=201)
def signup(
    user_create: UserCreateDTO,
    auth_service: AuthService = Depends(get_auth_service),
):
    # 1. Create the user
    auth_service.register_user(user_create)
    
    # 2. Immediately authenticate them to get a token
    return auth_service.authenticate_user(user_create.username, user_create.password)

@router.post("/signup", response_model=TokenResponseDTO, status_code=201)
def signup(
    signup_dto: SignupRequestDTO,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Register a new user and return JWT access token.

    Args:
        signup_dto: User signup information (username, password, name, preferences)
        auth_service: Injected authentication service

    Returns:
        TokenResponseDTO with JWT access token

    Raises:
        HTTPException: 400 if username already exists
    """
    return auth_service.signup_user(signup_dto)


@router.post("/logout")
def logout():
    return {"message": "Successfully logged out"}