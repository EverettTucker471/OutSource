from pydantic import BaseModel, Field
from typing import Optional


class CircleResponseDTO(BaseModel):
    """Response model for circle information."""

    id: int
    name: str
    public: bool
    owner: int

    class Config:
        from_attributes = True


class CircleBasicDTO(BaseModel):
    """Basic circle information without owner details."""

    id: int
    name: str
    public: bool

    class Config:
        from_attributes = True


class CircleCreateDTO(BaseModel):
    """DTO for creating a new circle."""

    name: str = Field(..., min_length=1, max_length=255, description="Circle name")
    public: bool = Field(default=False, description="Whether the circle is public")


class CircleUpdateDTO(BaseModel):
    """DTO for updating circle information."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Circle name")
    public: Optional[bool] = Field(None, description="Whether the circle is public")
