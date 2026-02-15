from pydantic import BaseModel
from typing import Any


class RecommendationInput(BaseModel):
    """Input data sent to Gemini for generating recommendations"""
    weather_data: Any  # Format depends on weather API response
    preferences: list[str]


class RecommendationResult(BaseModel):
    """Result returned from Gemini recommendation"""
    activity_name: str
    activity_description: str
