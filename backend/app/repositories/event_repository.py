from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.event import Event
from app.models.associations import EventOwnership


class EventRepository:
    """Repository for managing events."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, event_id: int) -> Optional[Event]:
        """Get event by ID."""
        return self.db.query(Event).filter(Event.id == event_id).first()

    def create(self, event: Event) -> Event:
        """Create a new event."""
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def update(self, event: Event) -> Event:
        """Update an existing event."""
        self.db.commit()
        self.db.refresh(event)
        return event

    def delete(self, event: Event) -> None:
        """Delete an event."""
        self.db.delete(event)
        self.db.commit()

    def get_events_for_user(self, user_id: int) -> List[Event]:
        """Get all events for a user."""
        ownerships = self.db.query(EventOwnership).filter(
            EventOwnership.user_id == user_id
        ).all()

        event_ids = [o.event_id for o in ownerships]
        return self.db.query(Event).filter(Event.id.in_(event_ids)).all() if event_ids else []

    def owns_event(self, user_id: int, event_id: int) -> bool:
        """Check if user owns/has access to event."""
        return self.db.query(EventOwnership).filter(
            EventOwnership.user_id == user_id,
            EventOwnership.event_id == event_id
        ).first() is not None

    def add_owner(self, user_id: int, event_id: int) -> EventOwnership:
        """Add a user as owner of an event."""
        ownership = EventOwnership(user_id=user_id, event_id=event_id)
        self.db.add(ownership)
        self.db.commit()
        self.db.refresh(ownership)
        return ownership
