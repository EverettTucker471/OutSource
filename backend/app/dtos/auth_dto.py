from pydantic import BaseModel, Field
from typing import List, Optional


class LoginRequestDTO(BaseModel):
    """Request model for user login."""

    username: str = Field(..., min_length=1, description="Username for authentication")
    password: str = Field(..., min_length=1, description="Password for authentication")


class SignupRequestDTO(BaseModel):
    """Request model for user signup."""

    username: str = Field(..., min_length=1, max_length=255, description="Desired username")
    password: str = Field(..., min_length=1, description="Password for the account")
    name: str = Field(..., min_length=1, max_length=255, description="User's display name")
    preferences: Optional[List[str]] = Field(default_factory=list, description="User preferences")


class TokenResponseDTO(BaseModel):
    """Response model for successful login."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
