from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class EventResponseDTO(BaseModel):
    """Response model for event information."""

    id: int
    name: str
    description: Optional[str]
    start_at: datetime
    end_at: datetime
    state: str

    class Config:
        from_attributes = True


class EventCreateDTO(BaseModel):
    """DTO for creating a new event."""

    name: str = Field(..., min_length=1, max_length=255, description="Event name")
    description: Optional[str] = Field(None, max_length=1000, description="Event description")
    start_at: datetime = Field(..., description="Event start time")
    end_at: datetime = Field(..., description="Event end time")


class EventUpdateDTO(BaseModel):
    """DTO for updating event information."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Event name")
    description: Optional[str] = Field(None, max_length=1000, description="Event description")
    start_at: Optional[datetime] = Field(None, description="Event start time")
    end_at: Optional[datetime] = Field(None, description="Event end time")
    state: Optional[str] = Field(None, description="Event state (upcoming, passed)")
