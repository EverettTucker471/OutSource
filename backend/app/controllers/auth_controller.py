from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

# Make sure you import these DTOs!
from app.dtos.user_dto import UserCreateDTO, UserResponseDTO
from app.dtos.auth_dto import LoginRequestDTO, TokenResponseDTO
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(tags=["authentication"])

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    user_repository = UserRepository(db)
    return AuthService(user_repository)

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

@router.post("/logout")
def logout():
    return {"message": "Successfully logged out"}