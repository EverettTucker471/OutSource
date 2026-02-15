from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth_dependency import get_current_user
from app.models.user import User

from app.repositories.user_repository import UserRepository
from app.repositories.friend_repository import FriendRepository
from app.repositories.circle_repository import CircleRepository
from app.repositories.event_repository import EventRepository
from app.repositories.friend_request_repository import FriendRequestRepository

from app.services.me_service import MeService

from app.dtos.user_dto import UserBasicDTO, UserResponseDTO, PreferencesUpdateDTO
from app.dtos.circle_dto import CircleResponseDTO
from app.dtos.event_dto import EventResponseDTO
from app.dtos.friend_request_dto import FriendRequestWithUserDTO

router = APIRouter(prefix="/me", tags=["me"])


def get_me_service(db: Session = Depends(get_db)) -> MeService:
    """Dependency to create MeService instance."""
    user_repository = UserRepository(db)
    friend_repository = FriendRepository(db)
    circle_repository = CircleRepository(db)
    event_repository = EventRepository(db)
    friend_request_repository = FriendRequestRepository(db)

    return MeService(
        user_repository=user_repository,
        friend_repository=friend_repository,
        circle_repository=circle_repository,
        event_repository=event_repository,
        friend_request_repository=friend_request_repository
    )


@router.get("", response_model=UserResponseDTO)
def get_me(
    current_user: User = Depends(get_current_user),
    me_service: MeService = Depends(get_me_service)
):
    """
    Get current authenticated user information (except password).

    Returns:
        UserResponseDTO with user information
    """
    return me_service.get_current_user(current_user.id)


@router.get("/friends", response_model=List[UserBasicDTO])
def get_my_friends(
    current_user: User = Depends(get_current_user),
    me_service: MeService = Depends(get_me_service)
):
    """
    Get list of users that are friends with the current user.

    Returns:
        List of UserBasicDTO with friend information
    """
    return me_service.get_friends(current_user.id)


@router.get("/circles", response_model=List[CircleResponseDTO])
def get_my_circles(
    current_user: User = Depends(get_current_user),
    me_service: MeService = Depends(get_me_service)
):
    """
    Get circles that the current user belongs to.

    Returns:
        List of CircleResponseDTO with circle information
    """
    return me_service.get_circles(current_user.id)


@router.get("/events", response_model=List[EventResponseDTO])
def get_my_events(
    current_user: User = Depends(get_current_user),
    me_service: MeService = Depends(get_me_service)
):
    """
    Get events belonging to the current user.

    Returns:
        List of EventResponseDTO with event information
    """
    return me_service.get_events(current_user.id)


@router.get("/friend-requests/incoming", response_model=List[FriendRequestWithUserDTO])
def get_incoming_friend_requests(
    current_user: User = Depends(get_current_user),
    me_service: MeService = Depends(get_me_service)
):
    """
    Get friend requests coming TO the current user.

    Returns:
        List of FriendRequestWithUserDTO with request and user information
    """
    return me_service.get_incoming_friend_requests(current_user.id)


@router.get("/friend-requests/outgoing", response_model=List[FriendRequestWithUserDTO])
def get_outgoing_friend_requests(
    current_user: User = Depends(get_current_user),
    me_service: MeService = Depends(get_me_service)
):
    """
    Get friend requests coming FROM the current user.

    Returns:
        List of FriendRequestWithUserDTO with request and user information
    """
    return me_service.get_outgoing_friend_requests(current_user.id)


@router.put("/preferences", response_model=UserResponseDTO)
def update_my_preferences(
    preferences_dto: PreferencesUpdateDTO,
    current_user: User = Depends(get_current_user),
    me_service: MeService = Depends(get_me_service)
):
    """
    Update preference list for the current user.

    Args:
        preferences_dto: New preferences list

    Returns:
        UserResponseDTO with updated user information
    """
    return me_service.update_preferences(current_user.id, preferences_dto)
