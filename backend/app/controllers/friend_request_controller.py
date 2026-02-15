from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth_dependency import get_current_user
from app.models.user import User

from app.repositories.friend_request_repository import FriendRequestRepository
from app.repositories.friend_repository import FriendRepository
from app.repositories.user_repository import UserRepository

from app.services.friend_request_service import FriendRequestService

from app.dtos.friend_request_dto import (
    FriendRequestCreateDTO,
    FriendRequestAcceptDTO,
    FriendRequestResponseDTO
)

router = APIRouter(tags=["friend-requests"])


def get_friend_request_service(db: Session = Depends(get_db)) -> FriendRequestService:
    """Dependency to create FriendRequestService instance."""
    friend_request_repository = FriendRequestRepository(db)
    friend_repository = FriendRepository(db)
    user_repository = UserRepository(db)

    return FriendRequestService(
        friend_request_repository=friend_request_repository,
        friend_repository=friend_repository,
        user_repository=user_repository
    )


@router.post("/friend-requests", response_model=FriendRequestResponseDTO, status_code=status.HTTP_201_CREATED)
def create_friend_request(
    request_dto: FriendRequestCreateDTO,
    current_user: User = Depends(get_current_user),
    service: FriendRequestService = Depends(get_friend_request_service)
):
    """
    Create a new friend request.

    Args:
        request_dto: Contains recipient_id

    Returns:
        FriendRequestResponseDTO with created friend request
    """
    return service.create_friend_request(current_user.id, request_dto)


@router.post("/friend-requests/accept", status_code=status.HTTP_200_OK)
def accept_friend_request(
    accept_dto: FriendRequestAcceptDTO,
    current_user: User = Depends(get_current_user),
    service: FriendRequestService = Depends(get_friend_request_service)
):
    """
    Accept a friend request.

    Args:
        accept_dto: Contains sender_id

    Returns:
        Success message
    """
    return service.accept_friend_request(current_user.id, accept_dto)


@router.post("/friend-requests/{request_id}/reject", status_code=status.HTTP_200_OK)
def reject_friend_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    service: FriendRequestService = Depends(get_friend_request_service)
):
    """
    Reject a friend request.

    Args:
        request_id: ID of the friend request to reject

    Returns:
        Success message
    """
    return service.reject_friend_request(current_user.id, request_id)


@router.delete("/friend-requests/{request_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_friend_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    service: FriendRequestService = Depends(get_friend_request_service)
):
    """
    Cancel an outgoing friend request.

    Args:
        request_id: ID of the friend request to cancel

    Returns:
        Success message
    """
    return service.cancel_friend_request(current_user.id, request_id)


@router.delete("/friends/{friend_id}", status_code=status.HTTP_200_OK)
def unfriend(
    friend_id: int,
    current_user: User = Depends(get_current_user),
    service: FriendRequestService = Depends(get_friend_request_service)
):
    """
    Remove a friend / unfriend a user.

    Args:
        friend_id: ID of the friend to remove

    Returns:
        Success message
    """
    return service.unfriend(current_user.id, friend_id)
