from pydantic import BaseModel, Field
from typing import List, Optional


class WeatherRequest(BaseModel):
    lat: float = Field(default=35.78)
    lon: float = Field(default=-78.69)


class ForecastResponse(BaseModel):
    temperature: float = Field(default=70)  # Temperature in farenheit
    precipitation: float = Field(default=0)  # Probability of precip
    wind: float = Field(default=0)  # Wind speed mph
    description: str = Field(default="")  # Detailed description of forecast


class WeatherResponse(BaseModel):
    forecast: List[ForecastResponse]

