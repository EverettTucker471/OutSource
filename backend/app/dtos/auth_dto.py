from pydantic import BaseModel, Field


class LoginRequestDTO(BaseModel):
    """Request model for user login."""

    username: str = Field(..., min_length=1, description="Username for authentication")
    password: str = Field(..., min_length=1, description="Password for authentication")


class TokenResponseDTO(BaseModel):
    """Response model for successful login."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
