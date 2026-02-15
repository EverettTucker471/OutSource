import google.generativeai as genai
from typing import List
from fastapi import HTTPException

from app.config import settings
from app.dtos.recommendation_dto import RecommendationInput, RecommendationResult, RecommendationItem
from app.repositories.circle_repository import CircleRepository
from app.repositories.user_repository import UserRepository


class RecommendationService:
    """Service for generating activity recommendations using Google Gemini."""

    def __init__(
        self,
        user_repository: UserRepository,
        circle_repository: CircleRepository = None
    ):
        self.user_repository = user_repository
        self.circle_repository = circle_repository
        self._model = None

    @property
    def model(self):
        """Lazy-load Gemini model."""
        if self._model is None:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel("gemini-2.5-flash")
        return self._model

    def get_recommendations_for_user(self, user_id: int) -> RecommendationResult:
        """
        Get activity recommendations for a specific user based on their preferences.

        Args:
            user_id: ID of the user

        Returns:
            RecommendationResult with activity recommendation
        """
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        preferences = user.preferences if user.preferences else []

        # For now, use placeholder weather data
        weather_data = "temp 75 F low wind no precipitation"

        recommendation_input = RecommendationInput(
            weather_data=weather_data,
            preferences=preferences
        )

        return self._generate_recommendation(recommendation_input)

    def get_recommendations_for_circle(self, circle_id: int) -> RecommendationResult:
        """
        Get activity recommendations for a circle by combining all members' preferences.

        Args:
            circle_id: ID of the circle

        Returns:
            RecommendationResult with activity recommendation
        """
        if not self.circle_repository:
            raise HTTPException(status_code=500, detail="Circle repository not available")

        circle = self.circle_repository.get_by_id(circle_id)
        if not circle:
            raise HTTPException(status_code=404, detail="Circle not found")

        members = self.circle_repository.get_members(circle_id)

        # Combine all members' preferences
        combined_preferences = []
        for member in members:
            if member.preferences:
                combined_preferences.extend(member.preferences)

        # Remove duplicates while preserving order
        unique_preferences = list(dict.fromkeys(combined_preferences))

        # For now, use placeholder weather data
        weather_data = "temp 75 F low wind no precipitation"

        recommendation_input = RecommendationInput(
            weather_data=weather_data,
            preferences=unique_preferences
        )

        return self._generate_recommendation(recommendation_input)

    def _generate_recommendation(self, input_data: RecommendationInput) -> RecommendationResult:
        """
        Generate activity recommendations using Gemini API.

        Args:
            input_data: RecommendationInput with weather data and preferences

        Returns:
            RecommendationResult with two activity recommendations
        """
        # Build prompt for Gemini
        preferences_str = ", ".join(input_data.preferences) if input_data.preferences else "no specific preferences"

        prompt = f"""Based on the following weather conditions and user preferences, suggest TWO different outdoor or indoor activities.

Weather: {input_data.weather_data}
User Preferences: {preferences_str}

Please respond with ONLY the following format (no additional text):
Activity 1 Name: [name of first activity]
Activity 1 Description: [one sentence description]
Activity 2 Name: [name of second activity]
Activity 2 Description: [one sentence description]"""

        try:
            response = self.model.generate_content(prompt)

            # Check if response was blocked or has no text
            if not response or not response.parts:
                raise ValueError(f"Empty response from Gemini. Prompt feedback: {getattr(response, 'prompt_feedback', 'N/A')}")

            # Get the text from response
            response_text = response.text if hasattr(response, 'text') else None

            if not response_text:
                raise ValueError(f"No text in Gemini response. Response parts: {response.parts}")

            # Parse response
            lines = response_text.strip().split('\n')
            activity1_name = ""
            activity1_description = ""
            activity2_name = ""
            activity2_description = ""

            for line in lines:
                if line.startswith("Activity 1 Name:"):
                    activity1_name = line.replace("Activity 1 Name:", "").strip()
                elif line.startswith("Activity 1 Description:"):
                    activity1_description = line.replace("Activity 1 Description:", "").strip()
                elif line.startswith("Activity 2 Name:"):
                    activity2_name = line.replace("Activity 2 Name:", "").strip()
                elif line.startswith("Activity 2 Description:"):
                    activity2_description = line.replace("Activity 2 Description:", "").strip()

            if not activity1_name or not activity1_description or not activity2_name or not activity2_description:
                # If parsing failed, return the raw response for debugging
                raise ValueError(f"Could not parse Gemini response. Raw response: {response_text}")

            return RecommendationResult(
                recommendations=[
                    RecommendationItem(
                        activity_name=activity1_name,
                        activity_description=activity1_description
                    ),
                    RecommendationItem(
                        activity_name=activity2_name,
                        activity_description=activity2_description
                    )
                ]
            )

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Catch all other exceptions and wrap them
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate recommendation: {type(e).__name__}: {str(e)}"
            )
