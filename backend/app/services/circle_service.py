from typing import List
from fastapi import HTTPException, status

from app.repositories.circle_repository import CircleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.event_repository import EventRepository
from app.models.circle import Circle
from app.dtos.circle_dto import CircleCreateDTO, CircleUpdateDTO, CircleResponseDTO
from app.dtos.user_dto import UserBasicDTO
from app.dtos.event_dto import EventResponseDTO


class CircleService:
    """Service for managing circles."""

    def __init__(
        self,
        circle_repository: CircleRepository,
        user_repository: UserRepository,
        event_repository: EventRepository = None
    ):
        self.circle_repository = circle_repository
        self.user_repository = user_repository
        self.event_repository = event_repository

    def get_all_circles(self) -> List[CircleResponseDTO]:
        """Get all circles."""
        circles = self.circle_repository.get_all()
        return [CircleResponseDTO.model_validate(circle) for circle in circles]

    def get_circle_by_id(self, circle_id: int) -> CircleResponseDTO:
        """Get circle by ID."""
        circle = self.circle_repository.get_by_id(circle_id)
        if not circle:
            raise HTTPException(status_code=404, detail="Circle not found")
        return CircleResponseDTO.model_validate(circle)

    def create_circle(self, current_user_id: int, circle_dto: CircleCreateDTO) -> CircleResponseDTO:
        """Create a new circle."""
        circle = Circle(
            name=circle_dto.name,
            public=circle_dto.public,
            owner=current_user_id
        )

        created_circle = self.circle_repository.create(circle)

        # Automatically add the owner as a member
        self.circle_repository.add_member(current_user_id, created_circle.id)

        return CircleResponseDTO.model_validate(created_circle)

    def update_circle(self, current_user_id: int, circle_id: int, update_dto: CircleUpdateDTO) -> CircleResponseDTO:
        """Update circle details."""
        circle = self.circle_repository.get_by_id(circle_id)
        if not circle:
            raise HTTPException(status_code=404, detail="Circle not found")

        # Only owner can update circle
        if circle.owner != current_user_id:
            raise HTTPException(status_code=403, detail="Only the circle owner can update the circle")

        # Update fields if provided
        if update_dto.name is not None:
            circle.name = update_dto.name
        if update_dto.public is not None:
            circle.public = update_dto.public

        updated_circle = self.circle_repository.update(circle)
        return CircleResponseDTO.model_validate(updated_circle)

    def delete_circle(self, current_user_id: int, circle_id: int) -> dict:
        """Delete a circle and its related events."""
        circle = self.circle_repository.get_by_id(circle_id)
        if not circle:
            raise HTTPException(status_code=404, detail="Circle not found")

        # Only owner can delete circle
        if circle.owner != current_user_id:
            raise HTTPException(status_code=403, detail="Only the circle owner can delete the circle")

        # TODO: Delete related events when circle-event relationship is defined

        self.circle_repository.delete(circle)
        return {"message": "Circle deleted successfully"}

    def join_circle(self, current_user_id: int, circle_id: int) -> dict:
        """Allow current user to join a public circle."""
        circle = self.circle_repository.get_by_id(circle_id)
        if not circle:
            raise HTTPException(status_code=404, detail="Circle not found")

        # Only public circles can be joined freely
        if not circle.public:
            raise HTTPException(status_code=403, detail="Cannot join a private circle")

        # Check if already a member
        if self.circle_repository.is_member(current_user_id, circle_id):
            raise HTTPException(status_code=400, detail="Already a member of this circle")

        self.circle_repository.add_member(current_user_id, circle_id)
        return {"message": "Successfully joined circle"}

    def add_member_to_circle(self, current_user_id: int, circle_id: int, user_id: int) -> dict:
        """Add a user to a circle (only owner can do this)."""
        circle = self.circle_repository.get_by_id(circle_id)
        if not circle:
            raise HTTPException(status_code=404, detail="Circle not found")

        # Only owner can add members
        if circle.owner != current_user_id:
            raise HTTPException(status_code=403, detail="Only the circle owner can add members")

        # Verify user exists
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if already a member
        if self.circle_repository.is_member(user_id, circle_id):
            raise HTTPException(status_code=400, detail="User is already a member of this circle")

        self.circle_repository.add_member(user_id, circle_id)
        return {"message": "User added to circle successfully"}

    def leave_circle(self, current_user_id: int, circle_id: int) -> dict:
        """Allow current user to leave a circle."""
        circle = self.circle_repository.get_by_id(circle_id)
        if not circle:
            raise HTTPException(status_code=404, detail="Circle not found")

        # Owner cannot leave their own circle
        if circle.owner == current_user_id:
            raise HTTPException(status_code=400, detail="Circle owner cannot leave the circle. Delete it instead.")

        # Check if member
        if not self.circle_repository.is_member(current_user_id, circle_id):
            raise HTTPException(status_code=400, detail="Not a member of this circle")

        self.circle_repository.remove_member(current_user_id, circle_id)
        return {"message": "Successfully left circle"}

    def kick_member(self, current_user_id: int, circle_id: int, user_id: int) -> dict:
        """Kick a user from a circle (only owner can do this)."""
        circle = self.circle_repository.get_by_id(circle_id)
        if not circle:
            raise HTTPException(status_code=404, detail="Circle not found")

        # Only owner can kick members
        if circle.owner != current_user_id:
            raise HTTPException(status_code=403, detail="Only the circle owner can kick members")

        # Cannot kick yourself (owner)
        if user_id == current_user_id:
            raise HTTPException(status_code=400, detail="Cannot kick yourself from your own circle")

        # Check if user is a member
        if not self.circle_repository.is_member(user_id, circle_id):
            raise HTTPException(status_code=400, detail="User is not a member of this circle")

        self.circle_repository.remove_member(user_id, circle_id)
        return {"message": "User kicked from circle successfully"}

    def get_circle_members(self, circle_id: int) -> List[UserBasicDTO]:
        """Get all members of a circle."""
        circle = self.circle_repository.get_by_id(circle_id)
        if not circle:
            raise HTTPException(status_code=404, detail="Circle not found")

        members = self.circle_repository.get_members(circle_id)
        return [UserBasicDTO.model_validate(member) for member in members]

    def get_circle_events(self, circle_id: int) -> List[EventResponseDTO]:
        """Get all events for a circle."""
        circle = self.circle_repository.get_by_id(circle_id)
        if not circle:
            raise HTTPException(status_code=404, detail="Circle not found")

        # TODO: Implement when circle-event relationship is defined
        # For now, return empty list
        return []
