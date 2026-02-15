from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.associations import FriendRequests


class FriendRequestRepository:
    """Repository for managing friend requests."""

    def __init__(self, db: Session):
        self.db = db

    def get_incoming_requests(self, user_id: int) -> List[FriendRequests]:
        """Get all incoming friend requests for a user."""
        return self.db.query(FriendRequests).filter(
            FriendRequests.incoming_user_id == user_id,
            FriendRequests.status == "pending"
        ).all()

    def get_outgoing_requests(self, user_id: int) -> List[FriendRequests]:
        """Get all outgoing friend requests from a user."""
        return self.db.query(FriendRequests).filter(
            FriendRequests.outgoing_user_id == user_id,
            FriendRequests.status == "pending"
        ).all()

    def get_by_id(self, request_id: int) -> Optional[FriendRequests]:
        """Get friend request by ID."""
        return self.db.query(FriendRequests).filter(FriendRequests.id == request_id).first()

    def get_request(self, outgoing_user_id: int, incoming_user_id: int) -> Optional[FriendRequests]:
        """Get friend request between two users."""
        return self.db.query(FriendRequests).filter(
            FriendRequests.outgoing_user_id == outgoing_user_id,
            FriendRequests.incoming_user_id == incoming_user_id
        ).first()

    def create_request(self, outgoing_user_id: int, incoming_user_id: int) -> FriendRequests:
        """Create a new friend request."""
        request = FriendRequests(
            outgoing_user_id=outgoing_user_id,
            incoming_user_id=incoming_user_id,
            status="pending"
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def update_status(self, request_id: int, status: str) -> Optional[FriendRequests]:
        """Update friend request status."""
        request = self.get_by_id(request_id)
        if request:
            request.status = status
            self.db.commit()
            self.db.refresh(request)
        return request

    def delete_request(self, request_id: int) -> bool:
        """Delete a friend request."""
        request = self.get_by_id(request_id)
        if request:
            self.db.delete(request)
            self.db.commit()
            return True
        return False
