from typing import List
from fastapi import HTTPException, status

from app.repositories.friend_repository import FriendRepository
from app.repositories.circle_repository import CircleRepository
from app.repositories.event_repository import EventRepository
from app.repositories.friend_request_repository import FriendRequestRepository
from app.repositories.user_repository import UserRepository

from app.dtos.user_dto import UserBasicDTO, UserResponseDTO, PreferencesUpdateDTO
from app.dtos.circle_dto import CircleResponseDTO
from app.dtos.event_dto import EventResponseDTO
from app.dtos.friend_request_dto import FriendRequestWithUserDTO


class MeService:
    """Service for managing current user endpoints."""

    def __init__(
        self,
        user_repository: UserRepository,
        friend_repository: FriendRepository,
        circle_repository: CircleRepository,
        event_repository: EventRepository,
        friend_request_repository: FriendRequestRepository
    ):
        self.user_repository = user_repository
        self.friend_repository = friend_repository
        self.circle_repository = circle_repository
        self.event_repository = event_repository
        self.friend_request_repository = friend_request_repository

    def get_current_user(self, user_id: int) -> UserResponseDTO:
        """Get current user information."""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponseDTO.model_validate(user)

    def get_friends(self, user_id: int) -> List[UserBasicDTO]:
        """Get all friends for current user."""
        friends = self.friend_repository.get_friends_for_user(user_id)
        return [UserBasicDTO.model_validate(friend) for friend in friends]

    def get_circles(self, user_id: int) -> List[CircleResponseDTO]:
        """Get all circles for current user."""
        circles = self.circle_repository.get_circles_for_user(user_id)
        return [CircleResponseDTO.model_validate(circle) for circle in circles]

    def get_events(self, user_id: int) -> List[EventResponseDTO]:
        """Get all events for current user."""
        events = self.event_repository.get_events_for_user(user_id)
        return [EventResponseDTO.model_validate(event) for event in events]

    def get_incoming_friend_requests(self, user_id: int) -> List[FriendRequestWithUserDTO]:
        """Get incoming friend requests for current user."""
        requests = self.friend_request_repository.get_incoming_requests(user_id)
        result = []
        for request in requests:
            user = self.user_repository.get_by_id(request.outgoing_user_id)
            if user:
                result.append(FriendRequestWithUserDTO(
                    id=request.id,
                    user=UserBasicDTO.model_validate(user),
                    status=request.status
                ))
        return result

    def get_outgoing_friend_requests(self, user_id: int) -> List[FriendRequestWithUserDTO]:
        """Get outgoing friend requests for current user."""
        requests = self.friend_request_repository.get_outgoing_requests(user_id)
        result = []
        for request in requests:
            user = self.user_repository.get_by_id(request.incoming_user_id)
            if user:
                result.append(FriendRequestWithUserDTO(
                    id=request.id,
                    user=UserBasicDTO.model_validate(user),
                    status=request.status
                ))
        return result

    def update_preferences(self, user_id: int, preferences_dto: PreferencesUpdateDTO) -> UserResponseDTO:
        """Update user preferences."""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.preferences = preferences_dto.preferences
        updated_user = self.user_repository.update(user)
        return UserResponseDTO.model_validate(updated_user)
