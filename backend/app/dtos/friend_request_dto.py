from pydantic import BaseModel, Field
from app.dtos.user_dto import UserBasicDTO


class FriendRequestCreateDTO(BaseModel):
    """Request model for creating a friend request."""
    recipient_id: int = Field(..., description="ID of user to send friend request to")


class FriendRequestAcceptDTO(BaseModel):
    """Request model for accepting a friend request."""
    sender_id: int = Field(..., description="ID of user who sent the friend request")


class FriendRequestResponseDTO(BaseModel):
    """Response model for friend request information."""

    id: int
    outgoing_user_id: int
    incoming_user_id: int
    status: str

    class Config:
        from_attributes = True


class FriendRequestWithUserDTO(BaseModel):
    """Friend request with user information."""

    id: int
    user: UserBasicDTO
    status: str
