from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth_dependency import get_current_user
from app.models.user import User

from app.repositories.user_repository import UserRepository
from app.repositories.circle_repository import CircleRepository

from app.services.recommendation_service import RecommendationService

from app.dtos.recommendation_dto import RecommendationResult

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_recommendation_service(db: Session = Depends(get_db)) -> RecommendationService:
    """Dependency to create RecommendationService instance."""
    user_repository = UserRepository(db)
    circle_repository = CircleRepository(db)

    return RecommendationService(
        user_repository=user_repository,
        circle_repository=circle_repository
    )


@router.post("", response_model=RecommendationResult)
def get_user_recommendations(
    current_user: User = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Get activity recommendations for the current user based on their preferences.

    This endpoint uses Google Gemini AI to generate personalized activity recommendations
    based on the current user's preferences and weather conditions.

    Returns:
        RecommendationResult with activity name and description
    """
    return service.get_recommendations_for_user(current_user.id)


@router.post("/{circle_id}", response_model=RecommendationResult)
def get_circle_recommendations(
    circle_id: int,
    current_user: User = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Get activity recommendations for a circle by combining all members' preferences.

    This endpoint uses Google Gemini AI to generate group activity recommendations
    based on all circle members' preferences and weather conditions.

    Args:
        circle_id: ID of the circle

    Returns:
        RecommendationResult with activity name and description
    """
    return service.get_recommendations_for_circle(circle_id)
