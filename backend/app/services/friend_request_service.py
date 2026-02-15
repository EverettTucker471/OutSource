from fastapi import HTTPException, status
from app.repositories.friend_request_repository import FriendRequestRepository
from app.repositories.friend_repository import FriendRepository
from app.repositories.user_repository import UserRepository
from app.dtos.friend_request_dto import FriendRequestCreateDTO, FriendRequestAcceptDTO, FriendRequestResponseDTO


class FriendRequestService:
    """Service for managing friend requests and friendships."""

    def __init__(
        self,
        friend_request_repository: FriendRequestRepository,
        friend_repository: FriendRepository,
        user_repository: UserRepository
    ):
        self.friend_request_repository = friend_request_repository
        self.friend_repository = friend_repository
        self.user_repository = user_repository

    def create_friend_request(
        self,
        current_user_id: int,
        request_dto: FriendRequestCreateDTO
    ) -> FriendRequestResponseDTO:
        """Create a new friend request."""
        recipient_id = request_dto.recipient_id

        # Validate recipient exists
        recipient = self.user_repository.get_by_id(recipient_id)
        if not recipient:
            raise HTTPException(status_code=404, detail="Recipient user not found")

        # Can't send friend request to yourself
        if current_user_id == recipient_id:
            raise HTTPException(status_code=400, detail="Cannot send friend request to yourself")

        # Check if already friends
        if self.friend_repository.are_friends(current_user_id, recipient_id):
            raise HTTPException(status_code=400, detail="Already friends with this user")

        # Check if friend request already exists (either direction)
        existing_request = self.friend_request_repository.get_request(current_user_id, recipient_id)
        reverse_request = self.friend_request_repository.get_request(recipient_id, current_user_id)

        if existing_request and existing_request.status == "pending":
            raise HTTPException(status_code=400, detail="Friend request already sent")

        if reverse_request and reverse_request.status == "pending":
            raise HTTPException(status_code=400, detail="This user has already sent you a friend request")

        # Create the friend request
        friend_request = self.friend_request_repository.create_request(
            outgoing_user_id=current_user_id,
            incoming_user_id=recipient_id
        )

        return FriendRequestResponseDTO.model_validate(friend_request)

    def accept_friend_request(
        self,
        current_user_id: int,
        accept_dto: FriendRequestAcceptDTO
    ) -> dict:
        """Accept a friend request and create friendship."""
        sender_id = accept_dto.sender_id

        # Find the friend request
        friend_request = self.friend_request_repository.get_request(sender_id, current_user_id)

        if not friend_request:
            raise HTTPException(status_code=404, detail="Friend request not found")

        if friend_request.status != "pending":
            raise HTTPException(status_code=400, detail="Friend request is not pending")

        # Update request status to accepted
        self.friend_request_repository.update_status(friend_request.id, "accepted")

        # Create friendship
        self.friend_repository.add_friendship(sender_id, current_user_id)

        return {"message": "Friend request accepted"}

    def reject_friend_request(self, current_user_id: int, request_id: int) -> dict:
        """Reject a friend request."""
        friend_request = self.friend_request_repository.get_by_id(request_id)

        if not friend_request:
            raise HTTPException(status_code=404, detail="Friend request not found")

        # Only the recipient can reject the request
        if friend_request.incoming_user_id != current_user_id:
            raise HTTPException(status_code=403, detail="You can only reject requests sent to you")

        if friend_request.status != "pending":
            raise HTTPException(status_code=400, detail="Friend request is not pending")

        # Update status to rejected
        self.friend_request_repository.update_status(request_id, "rejected")

        return {"message": "Friend request rejected"}

    def cancel_friend_request(self, current_user_id: int, request_id: int) -> dict:
        """Cancel an outgoing friend request."""
        friend_request = self.friend_request_repository.get_by_id(request_id)

        if not friend_request:
            raise HTTPException(status_code=404, detail="Friend request not found")

        # Only the sender can cancel the request
        if friend_request.outgoing_user_id != current_user_id:
            raise HTTPException(status_code=403, detail="You can only cancel requests you sent")

        if friend_request.status != "pending":
            raise HTTPException(status_code=400, detail="Friend request is not pending")

        # Delete the friend request
        self.friend_request_repository.delete_request(request_id)

        return {"message": "Friend request cancelled"}

    def unfriend(self, current_user_id: int, friend_id: int) -> dict:
        """Remove a friendship."""
        # Validate friend exists
        friend = self.user_repository.get_by_id(friend_id)
        if not friend:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if they are actually friends
        if not self.friend_repository.are_friends(current_user_id, friend_id):
            raise HTTPException(status_code=400, detail="You are not friends with this user")

        # Remove friendship
        self.friend_repository.remove_friendship(current_user_id, friend_id)

        return {"message": "Friendship removed"}
