from passlib.context import CryptContext
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.dtos.user_dto import UserCreateDTO, UserResponseDTO, UserUpdateDTO
from typing import Optional
from fastapi import HTTPException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, user_dto: UserCreateDTO) -> UserResponseDTO:
        if self.user_repository.exists_by_username(user_dto.username):
            raise HTTPException(status_code=400, detail="Username already exists")

        hashed_password = pwd_context.hash(user_dto.password)

        user = User(
            username=user_dto.username,
            password=hashed_password,
            name=user_dto.name,
            preferences=user_dto.preferences,
            friends=user_dto.friends,
            groups=user_dto.groups,
            inc_requests=user_dto.inc_requests,
            out_requests=user_dto.out_requests
        )

        created_user = self.user_repository.create(user)
        return UserResponseDTO.model_validate(created_user)

    def get_user_by_id(self, user_id: int) -> UserResponseDTO:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponseDTO.model_validate(user)

    def get_user_by_username(self, username: str) -> Optional[UserResponseDTO]:
        user = self.user_repository.get_by_username(username)
        if not user:
            return None
        return UserResponseDTO.model_validate(user)

    def update_user(self, user_id: int, user_dto: UserUpdateDTO) -> UserResponseDTO:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user_dto.name is not None:
            user.name = user_dto.name
        if user_dto.preferences is not None:
            user.preferences = user_dto.preferences
        if user_dto.friends is not None:
            user.friends = user_dto.friends
        if user_dto.groups is not None:
            user.groups = user_dto.groups
        if user_dto.inc_requests is not None:
            user.inc_requests = user_dto.inc_requests
        if user_dto.out_requests is not None:
            user.out_requests = user_dto.out_requests

        updated_user = self.user_repository.update(user)
        return UserResponseDTO.model_validate(updated_user)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
