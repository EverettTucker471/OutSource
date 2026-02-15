from fastapi import HTTPException, status
from datetime import datetime

from app.repositories.event_repository import EventRepository
from app.models.event import Event, EventState
from app.dtos.event_dto import EventCreateDTO, EventUpdateDTO, EventResponseDTO


class EventService:
    """Service for managing events."""

    def __init__(self, event_repository: EventRepository):
        self.event_repository = event_repository

    def get_event_by_id(self, current_user_id: int, event_id: int) -> EventResponseDTO:
        """Get event by ID."""
        event = self.event_repository.get_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Check if user has access to this event
        if not self.event_repository.owns_event(current_user_id, event_id):
            raise HTTPException(status_code=403, detail="You do not have access to this event")

        return EventResponseDTO.model_validate(event)

    def create_event(self, current_user_id: int, event_dto: EventCreateDTO) -> EventResponseDTO:
        """Create a new event."""
        # Validate that end_at is after start_at
        if event_dto.end_at <= event_dto.start_at:
            raise HTTPException(
                status_code=400,
                detail="Event end time must be after start time"
            )

        # Determine initial state based on start time
        now = datetime.now()
        if event_dto.start_at > now:
            state = EventState.upcoming
        else:
            state = EventState.passed

        event = Event(
            name=event_dto.name,
            description=event_dto.description,
            start_at=event_dto.start_at,
            end_at=event_dto.end_at,
            state=state
        )

        created_event = self.event_repository.create(event)

        # Add creator as owner
        self.event_repository.add_owner(current_user_id, created_event.id)

        return EventResponseDTO.model_validate(created_event)

    def update_event(self, current_user_id: int, event_id: int, update_dto: EventUpdateDTO) -> EventResponseDTO:
        """Update event details."""
        event = self.event_repository.get_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Check if user owns this event
        if not self.event_repository.owns_event(current_user_id, event_id):
            raise HTTPException(status_code=403, detail="Only event owners can update the event")

        # Update fields if provided
        if update_dto.name is not None:
            event.name = update_dto.name
        if update_dto.description is not None:
            event.description = update_dto.description
        if update_dto.start_at is not None:
            event.start_at = update_dto.start_at
        if update_dto.end_at is not None:
            event.end_at = update_dto.end_at
        if update_dto.state is not None:
            # Validate state value
            try:
                event.state = EventState(update_dto.state)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid state. Must be one of: {', '.join([s.value for s in EventState])}"
                )

        # Validate that end_at is after start_at
        if event.end_at <= event.start_at:
            raise HTTPException(
                status_code=400,
                detail="Event end time must be after start time"
            )

        updated_event = self.event_repository.update(event)
        return EventResponseDTO.model_validate(updated_event)

    def delete_event(self, current_user_id: int, event_id: int) -> dict:
        """Delete an event."""
        event = self.event_repository.get_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")

        # Check if user owns this event
        if not self.event_repository.owns_event(current_user_id, event_id):
            raise HTTPException(status_code=403, detail="Only event owners can delete the event")

        self.event_repository.delete(event)
        return {"message": "Event deleted successfully"}
