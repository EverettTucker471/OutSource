from pydantic import BaseModel, Field
from app.dtos.user_dto import UserBasicDTO


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
