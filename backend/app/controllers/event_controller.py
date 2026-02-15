from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth_dependency import get_current_user
from app.models.user import User

from app.repositories.event_repository import EventRepository
from app.services.event_service import EventService

from app.dtos.event_dto import EventCreateDTO, EventUpdateDTO, EventResponseDTO

router = APIRouter(prefix="/events", tags=["events"])


def get_event_service(db: Session = Depends(get_db)) -> EventService:
    """Dependency to create EventService instance."""
    event_repository = EventRepository(db)
    return EventService(event_repository=event_repository)


@router.get("/{event_id}", response_model=EventResponseDTO)
def get_event_by_id(
    event_id: int,
    current_user: User = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    """
    Get a single specific event.
    User must be an owner of the event to view it.

    Args:
        event_id: ID of the event

    Returns:
        EventResponseDTO with event details
    """
    return service.get_event_by_id(current_user.id, event_id)


@router.post("", response_model=EventResponseDTO, status_code=status.HTTP_201_CREATED)
def create_event(
    event_dto: EventCreateDTO,
    current_user: User = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    """
    Create a new event.
    The creator is automatically added as an owner.

    Args:
        event_dto: Event creation data (name, description, start_at, end_at)

    Returns:
        EventResponseDTO with created event
    """
    return service.create_event(current_user.id, event_dto)


@router.put("/{event_id}", response_model=EventResponseDTO)
def update_event(
    event_id: int,
    update_dto: EventUpdateDTO,
    current_user: User = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    """
    Edit a specific event.
    Only event owners can update the event.

    Args:
        event_id: ID of the event to update
        update_dto: Updated event data

    Returns:
        EventResponseDTO with updated event
    """
    return service.update_event(current_user.id, event_id, update_dto)


@router.delete("/{event_id}", status_code=status.HTTP_200_OK)
def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    """
    Delete an event.
    Only event owners can delete the event.

    Args:
        event_id: ID of the event to delete

    Returns:
        Success message
    """
    return service.delete_event(current_user.id, event_id)
