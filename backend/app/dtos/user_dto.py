from pydantic import BaseModel, Field
from typing import List, Optional


class UserCreateDTO(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=255)
    preferences: Optional[List[str]] = Field(default_factory=list)

class UserBasicDTO(BaseModel):
    id: int
    username: str
    name: str

    class Config:
        from_attributes = True

class UserResponseDTO(BaseModel):
    id: int
    username: str
    name: str
    preferences: List[str]

    class Config:
        from_attributes = True


class UserUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    preferences: Optional[List[str]] = None
