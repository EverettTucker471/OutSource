import google.generativeai as genai
import httpx
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

    async def _fetch_weather_data(self, lat: float = 35.78, lon: float = -78.69) -> str:
        """
        Fetch weather data from NWS API and format it for Gemini prompt.
        Returns a 4-day forecast (8 periods covering day/night cycles).

        Args:
            lat: Latitude (defaults to Raleigh, NC)
            lon: Longitude (defaults to Raleigh, NC)

        Returns:
            Formatted weather string for Gemini prompt with 4-day forecast
        """
        headers = {
            "User-Agent": "(outsource.com, contact@outsource.com)",
            "Accept": "application/geo+json"
        }

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
                # Get point metadata
                points_url = f"https://api.weather.gov/points/{round(lat, 4)},{round(lon, 4)}"
                points_resp = await client.get(points_url, headers=headers)
                points_resp.raise_for_status()
                points_data = points_resp.json()

                # Extract forecast URL
                properties = points_data.get("properties", {})
                forecast_url = properties.get("forecast") or points_data.get("forecast")

                if not forecast_url:
                    # Fallback to placeholder if API fails
                    return "temp 75 F low wind no precipitation"

                # Get forecast
                forecast_resp = await client.get(forecast_url, headers=headers)
                forecast_resp.raise_for_status()
                forecast_data = forecast_resp.json()

                # Parse first 8 periods (approximately 4 days - day/night cycles)
                properties = forecast_data.get("properties", {})
                periods = properties.get("periods") or forecast_data.get("periods", [])

                if not periods:
                    return "temp 75 F low wind no precipitation"

                # Collect forecast for next 4 days (up to 8 periods)
                forecast_summary = []
                for i, period in enumerate(periods[:8]):
                    temp = period.get("temperature", 70)
                    wind = period.get("windSpeed", "calm")
                    precip = period.get("probabilityOfPrecipitation")

                    # Handle precipitation (may be dict or scalar)
                    if isinstance(precip, dict):
                        precip_val = precip.get("value", 0)
                    else:
                        precip_val = precip if precip is not None else 0

                    period_name = period.get("name", f"Period {i+1}")
                    short_forecast = period.get("shortForecast", "")

                    # Format: "Today: 75°F, wind 5 mph, 20% precip, Partly Cloudy"
                    precip_desc = f"{precip_val}% precip" if precip_val > 0 else "no precip"
                    forecast_summary.append(
                        f"{period_name}: {temp}°F, wind {wind}, {precip_desc}, {short_forecast}"
                    )

                # Join all periods with newlines for better readability
                return "\n".join(forecast_summary)

        except Exception as e:
            # Fallback to placeholder on any error
            return "temp 75 F low wind no precipitation"

    async def get_recommendations_for_user(self, user_id: int) -> RecommendationResult:
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

        # Fetch real weather data
        weather_data = await self._fetch_weather_data()

        recommendation_input = RecommendationInput(
            weather_data=weather_data,
            preferences=preferences
        )

        return self._generate_recommendation(recommendation_input)

    async def get_recommendations_for_circle(self, circle_id: int) -> RecommendationResult:
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

        # Fetch real weather data
        weather_data = await self._fetch_weather_data()

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
