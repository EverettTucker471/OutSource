from typing import List
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.dtos.user_dto import UserCreateDTO, UserResponseDTO, UserBasicDTO
from app.dependencies.auth_dependency import get_current_user as get_authenticated_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    user_repository = UserRepository(db)
    return UserService(user_repository)


@router.get("/current", response_model=UserResponseDTO)
def get_current_user(
    current_user: User = Depends(get_authenticated_user),
):
    """
    Get currently authenticated user from JWT token.
    """
    return UserResponseDTO.model_validate(current_user)


@router.get("/{user_id}", response_model=UserResponseDTO)
def get_user_by_id(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_authenticated_user),
):
    return user_service.get_user_by_id(user_id)


@router.get("", response_model=List[UserBasicDTO])
def get_all_users(
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_authenticated_user),
):
    return user_service.get_all_users()
