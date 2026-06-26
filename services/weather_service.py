# Weather and Air Quality data service
# Handles API URL construction, data fetching, and parsing

from config import (
    LAT,
    LON,
    AQICN_CITY_ID,
    AQICN_API_KEY,
    HTTP_TIMEOUT_SECONDS,
)
from services.api_client import fetch_json


def get_weather_data():
    """
    Fetches current weather data from Open-Meteo API.

    Returns:
        dict or None: Parsed weather data on success, None on failure
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "current": [
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "wind_speed_10m",
            "weather_code",
            "cloud_cover",
        ],
        "forecast_days": 1,
        "wind_speed_unit": "mph",
        "temperature_unit": "fahrenheit",
        "precipitation_unit": "inch",
    }
    return fetch_json(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)


def get_aqi_data():
    """
    Fetches Air Quality Index data from WAQI (World Air Quality Index).

    Returns:
        dict or None Parsed AQI data on success, None on failure
    """
    # Fetching by City ID
    url = f"https://api.waqi.info/feed/@{AQICN_CITY_ID}/"
    params = {"token": AQICN_API_KEY}
    return fetch_json(url, params=params, timeout=HTTP_TIMEOUT_SECONDS)


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

    WEATHER_CODES = {
        0: "Clear Sky",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Cloudy",
        45: "Foggy",
        48: "Rime Fog",
        51: "Light Drizzle",
        53: "Moderate Drizzle",
        55: "Heavy Drizzle",
        56: "Freez Drizzle",
        57: "Freez Drizzle",
        61: "Light Rain",
        63: "Rain",
        65: "Heavy Rain",
        66: "Freezing Rain",
        67: "Freezing Rain",
        71: "Light Snow",
        73: "Snow",
        75: "Heavy Snow",
        77: "Snow Grains",
        80: "Lgt Showers",
        81: "Showers",
        82: "Heavy Showers",
        85: "Lgt Snow Shwrs",
        86: "Snow Showers",
        95: "Thunderstorm",
        96: "Thunder w/Hail",
        99: "Thunder w/Hail",
    }

    try:
        current = weather_data["current"]
        raw_code = current.get("weather_code", 0)

        return {
            "temp": current["temperature_2m"],
            "desc": WEATHER_CODES.get(raw_code, f"Code: {raw_code}"),
            "feels_like": current["apparent_temperature"],
            "humidity": current["relative_humidity_2m"],
            "wind_speed": current["wind_speed_10m"],
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
        data_inner = aqi_data.get("data")
        if not isinstance(data_inner, dict):
            print(f"[WEATHER] 'data' field type: {type(data_inner).__name__}")
            raise TypeError("AQI 'data' field is not a dictionary")

        def get_num_val(val):
            if val is None:
                return None
            if isinstance(val, (int, float)):
                return val
            if isinstance(val, str):
                if val == "-" or val.strip() == "":
                    return None
                try:
                    return float(val)
                except ValueError:
                    return None
            return None

        raw_total = data_inner.get("aqi", {})
        total_aqi = get_num_val(raw_total)

        raw_iaqi = data_inner.get("iaqi", {})
        if not isinstance(raw_iaqi, dict):
            print("[WEATHER] 'iaqi' is not a dictionary!")
            raw_iaqi = {}

        cleaned_iaqi = {}
        for key, val in raw_iaqi.items():
            cleaned_iaqi[key] = get_num_val(val.get("v"))
        else:
            cleaned_iaqi[key] = get_num_val(val)

        print(f"[WEATHER] Formatted {len(cleaned_iaqi)} pollutants")
        return {
            "total_aqi": total_aqi,
            "iaqi": cleaned_iaqi,
        }
    except (KeyError, TypeError) as e:
        print(f"[WEATHER] Parse error: {e}")
        return None
