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
