import re
import httpx
import logging
from fastapi import APIRouter, HTTPException, status, Query
from app.dtos.weather_dto import WeatherResponse, ForecastResponse

# Set up a simple logger to help debug NWS responses
logger = logging.getLogger("weather_api")
logging.basicConfig(level=logging.INFO)

router = APIRouter(tags=["weather"])

# --- Helper Methods ---

def extract_wind_speed(wind_str: str) -> float:
    """
    Parses NWS wind strings like "5 mph", "5 to 8 mph", or "Calm".
    Returns the higher value in a range or 0 if no number is found.
    Handles None or non-string inputs gracefully.
    """
    if not isinstance(wind_str, str) or not wind_str or "Calm" in wind_str:
        return 0.0
    
    # Find all numbers in the string
    numbers = re.findall(r'\d+', wind_str)
    if not numbers:
        return 0.0
    
    # If it's a range "5 to 8", we take the 8 (conservative estimate)
    return float(max(map(int, numbers)))

def safe_float(value, default=0.0):
    """Safely converts value to float, handling None and strings."""
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

# --- API Endpoint ---

@router.get("/weather", response_model=WeatherResponse)
async def get_weather(
    lat: float = Query(..., description="Latitude (e.g., 35.77)"), 
    lon: float = Query(..., description="Longitude (e.g., -78.96)")
):
    """
    Fetches a 7-day forecast from weather.gov based on lat/lon coordinates.
    """
    # Round to 4 decimals to keep NWS happy and ensure formatting is clean
    lat_val = round(lat, 4)
    lon_val = round(lon, 4)

    headers = {
        "User-Agent": "(outsource.com, contact@outsource.com)",
        "Accept": "application/geo+json" 
    }

    # Use a 10s timeout to prevent hanging on NWS latency spikes
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        # Step 1: Get the metadata for the lat/lon
        # formatting explicitly as string to avoid any scientific notation
        points_url = f"https://api.weather.gov/points/{lat_val},{lon_val}"
        
        try:
            points_resp = await client.get(points_url, headers=headers)
            points_resp.raise_for_status()
            points_data = points_resp.json()
        except httpx.HTTPStatusError as e:
            detail = "Coordinates may be outside NWS coverage area (US only)." if e.response.status_code == 404 else "Error fetching point metadata"
            raise HTTPException(status_code=e.response.status_code, detail=detail)
        except httpx.ConnectTimeout:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="NWS API connection timed out")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error in points request: {str(e)}")

        # Step 2: Extract the forecast URL
        # Robustness Update: Check 'properties' (GeoJSON) AND root (JSON-LD)
        properties = points_data.get("properties", {})
        forecast_url = properties.get("forecast")
        
        if not forecast_url:
            # Fallback: check root level (matches the JSON you pasted)
            forecast_url = points_data.get("forecast")

        if not forecast_url:
            # Check for NWS soft errors
            if "title" in points_data and "status" in points_data:
                 logger.error(f"NWS Soft Error: {points_data}")
                 raise HTTPException(status_code=404, detail=f"NWS Error: {points_data.get('detail', 'Unknown error')}")
            
            # DEBUG: Log the full response to see why it's missing
            logger.error(f"Missing forecast URL. NWS Response for {points_url}: {points_data}")
            raise HTTPException(
                status_code=404, 
                detail=f"Forecast data not available for this location. Keys found: {list(points_data.keys())}"
            )

        # Step 3: Get the actual forecast periods
        try:
            forecast_resp = await client.get(forecast_url, headers=headers)
            forecast_resp.raise_for_status()
            forecast_data = forecast_resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail="Error fetching forecast grid data")
        
        # Step 4: Parse NWS 'periods'
        # Robustness Update: Check 'properties' (GeoJSON) AND root (JSON-LD)
        properties = forecast_data.get("properties", {})
        periods = properties.get("periods")

        if not periods:
            # Fallback: check root level
            periods = forecast_data.get("periods", [])
        
        parsed_forecasts = []
        for period in periods:
            temp_val = period.get("temperature", 70)
            
            # Handle Precip
            precip_raw = period.get("probabilityOfPrecipitation")
            if isinstance(precip_raw, dict):
                precip_val = precip_raw.get("value")
            else:
                precip_val = precip_raw
            
            forecast_item = ForecastResponse(
                temperature=safe_float(temp_val, 70.0),
                precipitation=safe_float(precip_val, 0.0),
                wind=extract_wind_speed(period.get("windSpeed", "")),
                description=str(period.get("detailedForecast", ""))
            )
            parsed_forecasts.append(forecast_item)

        return WeatherResponse(forecast=parsed_forecasts)
    