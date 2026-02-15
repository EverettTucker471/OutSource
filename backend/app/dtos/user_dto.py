from pydantic import BaseModel, Field
from typing import List, Optional


class UserCreateDTO(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=255)
    friends: Optional[List[int]] = Field(default_factory=list)
    groups: Optional[List[int]] = Field(default_factory=list)
    preferences: Optional[List[str]] = Field(default_factory=list)
    inc_requests: Optional[List[int]] = Field(default_factory=list)
    out_requests: Optional[List[int]] = Field(default_factory=list)

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
    friends: List[int]
    groups: List[int]
    preferences: List[str]
    inc_requests: List[int]
    out_requests: List[int]

    class Config:
        from_attributes = True


class UserUpdateDTO(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    friends: Optional[List[int]] = None
    groups: Optional[List[int]] = None
    preferences: Optional[List[str]] = None
    inc_requests: Optional[List[int]] = None
    out_requests: Optional[List[int]] = None
