from pydantic import BaseModel, Field


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
