from sqlalchemy import Column, Integer, ForeignKey, String, Table, UniqueConstraint
from .base import Base


class Friends(Base):
    """Join table for user friendships (many-to-many)"""
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="unique_friendship"),
    )

    def __repr__(self):
        return f"<Friends(user1_id={self.user1_id}, user2_id={self.user2_id})>"


class CircleMembership(Base):
    """Join table for circle memberships (many-to-many)"""
    __tablename__ = "circle_membership"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    circle_id = Column(Integer, ForeignKey("circles.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "circle_id", name="unique_membership"),
    )

    def __repr__(self):
        return f"<CircleMembership(user_id={self.user_id}, circle_id={self.circle_id})>"


class FriendRequests(Base):
    """Join table for friend requests (many-to-many)"""
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    outgoing_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    incoming_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, accepted, rejected

    __table_args__ = (
        UniqueConstraint("outgoing_user_id", "incoming_user_id", name="unique_friend_request"),
    )

    def __repr__(self):
        return f"<FriendRequests(outgoing_user_id={self.outgoing_user_id}, incoming_user_id={self.incoming_user_id}, status='{self.status}')>"


class EventOwnership(Base):
    """Join table for event ownership (many-to-many)"""
    __tablename__ = "event_ownership"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="unique_event_ownership"),
    )

    def __repr__(self):
        return f"<EventOwnership(user_id={self.user_id}, event_id={self.event_id})>"
