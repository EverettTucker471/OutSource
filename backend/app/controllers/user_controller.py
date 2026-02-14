from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.dtos.user_dto import UserCreateDTO, UserResponseDTO

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    user_repository = UserRepository(db)
    return UserService(user_repository)


@router.post("", response_model=UserResponseDTO, status_code=201)
def create_user(
    user_dto: UserCreateDTO,
    user_service: UserService = Depends(get_user_service)
):
    return user_service.create_user(user_dto)


@router.get("/current", response_model=UserResponseDTO)
def get_current_user(
    x_user_id: int = Header(..., description="Current user ID"),
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_user_by_id(x_user_id)


@router.get("/{user_id}", response_model=UserResponseDTO)
def get_user_by_id(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    return user_service.get_user_by_id(user_id)
