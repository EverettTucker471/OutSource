from fastapi import HTTPException, status
from app.dtos.auth_dto import TokenResponseDTO
from app.utils.jwt_utils import create_access_token
from app.dtos.user_dto import UserCreateDTO, UserResponseDTO
from app.repositories.user_repository import UserRepository
from app.models.user import User  # <--- CRITICAL IMPORT: You need this to create the object

class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def authenticate_user(self, username: str, password: str) -> TokenResponseDTO:
        user = self.user_repository.get_by_username(username)

        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if user is None:
            raise credentials_exception

        # FIX 1: Direct comparison since you are NOT hashing passwords yet
        if user.password != password:
            raise credentials_exception

        access_token = create_access_token(data={"sub": str(user.id)})
        return TokenResponseDTO(access_token=access_token, token_type="bearer")
    
    def register_user(self, user_create: UserCreateDTO) -> UserResponseDTO:
        if self.user_repository.get_by_username(user_create.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Prepare the data
        user_data = user_create.model_dump() 
        # Explicitly set the plain text password (since you aren't hashing)
        user_data["password"] = user_create.password

        # FIX 2: Convert the dictionary into a SQLAlchemy User Object
        # The ** syntax unpacks the dict: User(username="...", password="...", ...)
        new_user_instance = User(**user_data)

        # Now the repository receives the Object it expects
        saved_user = self.user_repository.create(new_user_instance)

        return UserResponseDTO.model_validate(saved_user)