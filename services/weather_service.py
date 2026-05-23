# Weather and Air Quality data service
# Handles API URL construction, data fetching, and parsing

from config import (
    OPENWEATHER_API_KEY,
    LAT,
    LON,
    AQICN_CITY_ID,
    AQICN_API_KEY,
    HTTP_TIMEOUT_SECONDS,
)
from services.api_client import fetch_json


def get_weather_data():
    """
    Fetches current weather data from OpenWeatherMap OneCall API.

    Returns:
        dict or None: Parsed weather data on success, None on failure
    """
    # Using the OneCall 3.0 endpoint
    # Excluding minutely, hourly, daily, alerts to save bandwidth
    url = (
        f"https://api.openweathermap.org/data/3.0/onecall?"
        f"lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}"
        f"&units=imperial&exclude=minutely,hourly,daily,alerts"
    )
    return fetch_json(url, timeout=HTTP_TIMEOUT_SECONDS)


def get_aqi_data():
    """
    Fetches Air Quality Index data from WAQI (World Air Quality Index).

    Returns:
        dict or None Parsed AQI data on success, None on failure
    """
    # Fetching by City ID
    url = f"https://api.waqi.info/feed/@{AQICN_CITY_ID}/?token={AQICN_API_KEY}"
    return fetch_json(url, timeout=HTTP_TIMEOUT_SECONDS)


def fetch_all_data():
    """
    Orchestrates fetching both weather and AQI data.

    Returns:
        tuple: (weather_data, aqi_data)
    """
    weather = get_weather_data()
    aqi = get_aqi_data()
    return weather, aqi


def format_weather_display(weather_data):
    """
    Extracts and formats weather data for display.

    Args:
        weather_data (dict): Raw weather JSON from API

    Returns:
        dict: Formatted data suitable for display rendering
    """
    if not weather_data or "current" not in weather_data:
        return None

    try:
        current = weather_data["current"]
        return {
            "temp": current["temp"],
            "desc": current["weather"][0]["description"],
            "feels_like": current["feels_like"],
            "humidity": current["humidity"],
            "wind_speed": current["wind_speed"],
        }
    except KeyError as e:
        print(f"[WEATHER] Missing key: {e}")
        return None


def format_aqi_display(aqi_data):
    """
    Extracts and formats AQI data for display.

    Args:
        aqi_data (dict): Raw AQI JSON from API

    Returns:
        dict: Formatted data suitable for display rendering
    """
    if not aqi_data:
        return None

    try:
        aqi_data_inner = aqi_data.get("data")
        if not isinstance(aqi_data_inner, dict):
            raise TypeError("AQI 'data' field is not a dictionary")

        return {
            "total_aqi": aqi_data_inner.get("aqi", 0),
            "iaqi": aqi_data_inner.get("iaqi", {}),
        }
    except (KeyError, TypeError) as e:
        print(f"[WEATHER] Parse error: {e}")
        return None
