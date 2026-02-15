from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.circle import Circle
from app.models.associations import CircleMembership


class CircleRepository:
    """Repository for managing circles."""

    def __init__(self, db: Session):
        self.db = db

    def get_circles_for_user(self, user_id: int) -> List[Circle]:
        """Get all circles a user belongs to."""
        memberships = self.db.query(CircleMembership).filter(
            CircleMembership.user_id == user_id
        ).all()

        circle_ids = [m.circle_id for m in memberships]
        return self.db.query(Circle).filter(Circle.id.in_(circle_ids)).all() if circle_ids else []

    def get_by_id(self, circle_id: int) -> Optional[Circle]:
        """Get circle by ID."""
        return self.db.query(Circle).filter(Circle.id == circle_id).first()

    def is_member(self, user_id: int, circle_id: int) -> bool:
        """Check if user is a member of circle."""
        return self.db.query(CircleMembership).filter(
            CircleMembership.user_id == user_id,
            CircleMembership.circle_id == circle_id
        ).first() is not None

    def add_member(self, user_id: int, circle_id: int) -> CircleMembership:
        """Add a user to a circle."""
        membership = CircleMembership(user_id=user_id, circle_id=circle_id)
        self.db.add(membership)
        self.db.commit()
        self.db.refresh(membership)
        return membership

    def remove_member(self, user_id: int, circle_id: int) -> bool:
        """Remove a user from a circle."""
        membership = self.db.query(CircleMembership).filter(
            CircleMembership.user_id == user_id,
            CircleMembership.circle_id == circle_id
        ).first()

        if membership:
            self.db.delete(membership)
            self.db.commit()
            return True
        return False
