from typing import List
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.friend_repository import FriendRepository
from app.repositories.circle_repository import CircleRepository
from app.services.user_service import UserService
from app.dtos.user_dto import UserCreateDTO, UserResponseDTO, UserBasicDTO
from app.dtos.circle_dto import CircleResponseDTO
from app.dependencies.auth_dependency import get_current_user as get_authenticated_user
from app.models.user import User

router = APIRouter(tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    user_repository = UserRepository(db)
    friend_repository = FriendRepository(db)
    circle_repository = CircleRepository(db)
    return UserService(user_repository, friend_repository, circle_repository)


@router.get("/{user_id}", response_model=UserResponseDTO)
def get_user_by_id(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_authenticated_user),
):
    return user_service.get_user_by_id(user_id)


@router.get("/", response_model=List[UserBasicDTO])
def get_all_users(
    user_service: UserService = Depends(get_user_service),
    # current_user: User = Depends(get_authenticated_user),
):
    return user_service.get_all_users()


@router.get("/{user_id}/friends", response_model=List[UserBasicDTO])
def get_user_friends(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_authenticated_user),
):
    """
    Get list of friends for a specific user.

    Args:
        user_id: ID of the user to get friends for

    Returns:
        List of UserBasicDTO with friend information
    """
    return user_service.get_user_friends(user_id)


@router.get("/{user_id}/circles", response_model=List[CircleResponseDTO])
def get_user_circles(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_authenticated_user),
):
    """
    Get list of circles a specific user belongs to.

    Args:
        user_id: ID of the user to get circles for

    Returns:
        List of CircleResponseDTO with circle information
    """
    return user_service.get_user_circles(user_id)
