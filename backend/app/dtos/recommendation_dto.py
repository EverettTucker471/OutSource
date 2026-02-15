from pydantic import BaseModel
from typing import Any, List


class RecommendationInput(BaseModel):
    """Input data sent to Gemini for generating recommendations"""
    weather_data: Any  # Format depends on weather API response
    preferences: list[str]


class RecommendationItem(BaseModel):
    """Single activity recommendation"""
    activity_name: str
    activity_description: str


class RecommendationResult(BaseModel):
    """Result containing multiple recommendations"""
    recommendations: List[RecommendationItem]
