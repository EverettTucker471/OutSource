from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth_dependency import get_current_user
from app.models.user import User

from app.repositories.circle_repository import CircleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.event_repository import EventRepository

from app.services.circle_service import CircleService

from app.dtos.circle_dto import CircleCreateDTO, CircleUpdateDTO, CircleResponseDTO
from app.dtos.user_dto import UserBasicDTO
from app.dtos.event_dto import EventResponseDTO

router = APIRouter(prefix="/circles", tags=["circles"])


def get_circle_service(db: Session = Depends(get_db)) -> CircleService:
    """Dependency to create CircleService instance."""
    circle_repository = CircleRepository(db)
    user_repository = UserRepository(db)
    event_repository = EventRepository(db)

    return CircleService(
        circle_repository=circle_repository,
        user_repository=user_repository,
        event_repository=event_repository
    )


@router.get("", response_model=List[CircleResponseDTO])
def get_all_circles(
    current_user: User = Depends(get_current_user),
    service: CircleService = Depends(get_circle_service)
):
    """
    Get all circles (id, names).

    Returns:
        List of CircleResponseDTO with all circle information
    """
    return service.get_all_circles()


@router.get("/{circle_id}", response_model=CircleResponseDTO)
def get_circle_by_id(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    service: CircleService = Depends(get_circle_service)
):
    """
    Get circle details for a specific circle.

    Args:
        circle_id: ID of the circle

    Returns:
        CircleResponseDTO with circle details
    """
    return service.get_circle_by_id(circle_id)


@router.post("", response_model=CircleResponseDTO, status_code=status.HTTP_201_CREATED)
def create_circle(
    circle_dto: CircleCreateDTO,
    current_user: User = Depends(get_current_user),
    service: CircleService = Depends(get_circle_service)
):
    """
    Create a new circle.

    Args:
        circle_dto: Circle creation data (name, public)

    Returns:
        CircleResponseDTO with created circle
    """
    return service.create_circle(current_user.id, circle_dto)


@router.put("/{circle_id}", response_model=CircleResponseDTO)
def update_circle(
    circle_id: int,
    update_dto: CircleUpdateDTO,
    current_user: User = Depends(get_current_user),
    service: CircleService = Depends(get_circle_service)
):
    """
    Update circle details (name, privacy settings).
    Only the circle owner can update the circle.

    Args:
        circle_id: ID of the circle to update
        update_dto: Updated circle data

    Returns:
        CircleResponseDTO with updated circle
    """
    return service.update_circle(current_user.id, circle_id, update_dto)


@router.delete("/{circle_id}", status_code=status.HTTP_200_OK)
def delete_circle(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    service: CircleService = Depends(get_circle_service)
):
    """
    Delete the circle and its related events.
    Only the circle owner can delete the circle.

    Args:
        circle_id: ID of the circle to delete

    Returns:
        Success message
    """
    return service.delete_circle(current_user.id, circle_id)


@router.post("/{circle_id}/join", status_code=status.HTTP_200_OK)
def join_circle(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    service: CircleService = Depends(get_circle_service)
):
    """
    Allow current user to join a circle (that is public).

    Args:
        circle_id: ID of the circle to join

    Returns:
        Success message
    """
    return service.join_circle(current_user.id, circle_id)


@router.post("/{circle_id}/join/{user_id}", status_code=status.HTTP_200_OK)
def add_member_to_circle(
    circle_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: CircleService = Depends(get_circle_service)
):
    """
    Add a user to a circle by id.
    Only the circle owner can add members.

    Args:
        circle_id: ID of the circle
        user_id: ID of the user to add

    Returns:
        Success message
    """
    return service.add_member_to_circle(current_user.id, circle_id, user_id)


@router.post("/{circle_id}/leave", status_code=status.HTTP_200_OK)
def leave_circle(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    service: CircleService = Depends(get_circle_service)
):
    """
    Allow current user to leave a circle.
    Circle owner cannot leave their own circle.

    Args:
        circle_id: ID of the circle to leave

    Returns:
        Success message
    """
    return service.leave_circle(current_user.id, circle_id)


@router.post("/{circle_id}/kick/{user_id}", status_code=status.HTTP_200_OK)
def kick_member(
    circle_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: CircleService = Depends(get_circle_service)
):
    """
    Kick a user from a circle by id.
    Only the circle owner can kick members.

    Args:
        circle_id: ID of the circle
        user_id: ID of the user to kick

    Returns:
        Success message
    """
    return service.kick_member(current_user.id, circle_id, user_id)


@router.get("/{circle_id}/members", response_model=List[UserBasicDTO])
def get_circle_members(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    service: CircleService = Depends(get_circle_service)
):
    """
    Get list of members in a circle.

    Args:
        circle_id: ID of the circle

    Returns:
        List of UserBasicDTO with member information
    """
    return service.get_circle_members(circle_id)


@router.get("/{circle_id}/events", response_model=List[EventResponseDTO])
def get_circle_events(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    service: CircleService = Depends(get_circle_service)
):
    """
    Get events for a specific circle.

    Args:
        circle_id: ID of the circle

    Returns:
        List of EventResponseDTO with event information
    """
    return service.get_circle_events(circle_id)
