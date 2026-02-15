from typing import List
from sqlalchemy.orm import Session
from app.models.associations import Friends
from app.models.user import User


class FriendRepository:
    """Repository for managing user friendships."""

    def __init__(self, db: Session):
        self.db = db

    def get_friends_for_user(self, user_id: int) -> List[User]:
        """Get all friends for a user."""
        # Friends can be in either direction (user1_id or user2_id)
        friendships = self.db.query(Friends).filter(
            (Friends.user1_id == user_id) | (Friends.user2_id == user_id)
        ).all()

        friend_ids = []
        for friendship in friendships:
            if friendship.user1_id == user_id:
                friend_ids.append(friendship.user2_id)
            else:
                friend_ids.append(friendship.user1_id)

        return self.db.query(User).filter(User.id.in_(friend_ids)).all() if friend_ids else []

    def are_friends(self, user1_id: int, user2_id: int) -> bool:
        """Check if two users are friends."""
        return self.db.query(Friends).filter(
            ((Friends.user1_id == user1_id) & (Friends.user2_id == user2_id)) |
            ((Friends.user1_id == user2_id) & (Friends.user2_id == user1_id))
        ).first() is not None

    def add_friendship(self, user1_id: int, user2_id: int) -> Friends:
        """Create a new friendship."""
        friendship = Friends(user1_id=user1_id, user2_id=user2_id)
        self.db.add(friendship)
        self.db.commit()
        self.db.refresh(friendship)
        return friendship

    def remove_friendship(self, user1_id: int, user2_id: int) -> bool:
        """Remove a friendship."""
        friendship = self.db.query(Friends).filter(
            ((Friends.user1_id == user1_id) & (Friends.user2_id == user2_id)) |
            ((Friends.user1_id == user2_id) & (Friends.user2_id == user1_id))
        ).first()

        if friendship:
            self.db.delete(friendship)
            self.db.commit()
            return True
        return False
