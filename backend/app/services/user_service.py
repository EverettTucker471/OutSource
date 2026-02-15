from typing import List
from passlib.context import CryptContext
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.dtos.user_dto import UserCreateDTO, UserResponseDTO, UserUpdateDTO, UserBasicDTO
from typing import Optional
from fastapi import HTTPException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

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

    def get_all_users(self) -> List[UserBasicDTO]:
        user_list = self.user_repository.get_all()

        # For list endpoints, prefer returning [] instead of None
        if not user_list:
            return []

        return_list: List[UserBasicDTO] = []
        for user in user_list:
            dto = UserBasicDTO.model_validate(user)
            return_list.append(dto)

        return return_list

    def update_user(self, user_id: int, user_dto: UserUpdateDTO) -> UserResponseDTO:
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user_dto.name is not None:
            user.name = user_dto.name
        if user_dto.preferences is not None:
            user.preferences = user_dto.preferences

        updated_user = self.user_repository.update(user)
        return UserResponseDTO.model_validate(updated_user)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
