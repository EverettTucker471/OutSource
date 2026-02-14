from pydantic import BaseModel, Field
from typing import List, Optional


class UserCreateDTO(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=255)
    friends: Optional[List[int]] = Field(default_factory=list)
    groups: Optional[List[int]] = Field(default_factory=list)


class UserResponseDTO(BaseModel):
    id: int
    username: str
    name: str
    friends: List[int]
    groups: List[int]

    class Config:
        from_attributes = True


class UserUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    friends: Optional[List[int]] = None
    groups: Optional[List[int]] = None
