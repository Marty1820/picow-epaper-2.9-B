# Handles WiFi connectivity, Time Sync, and API Data Fetching

import network
import ntptime
import time
import utime
import urequests
from config import (
    SSID,
    PASSWORD,
    TIMEOUT_SECONDS,
    OPENWEATHER_API_KEY,
    LAT,
    LON,
    AQICN_CITY_ID,
    AQICN_API_KEY,
)


# --- WiFi Management ---
def connect_wifi(timeout=TIMEOUT_SECONDS):
    """
    Connects to the configured Wi-Fi network.
    Returns the WLAN object if successful, None otherwise.
    """
    print(f"[WiFi] Connecting to {SSID}...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"[WiFi] Already connected. IP: {ip}")
        return wlan

    wlan.connect(SSID, PASSWORD)

    start_time = utime.time()
    while not wlan.isconnected():
        if utime.time() - start_time > timeout:
            print("[WiFi] Connection timed out.")
            return None

        # Optional: Blink an LED or print progress every few seconds
        # if utime.ticks_diff(utime.time(), start_time) % 5 == 0:
        #     print(f"[WiFi] Waiting... ({int(timeout - (utime.time() - start_time))}s)")
        utime.sleep(1)

    ip = wlan.ifconfig()[0]
    print(f"[WiFi] Connected! IP: {ip}")
    return wlan


def disconnect_wifi(wlan):
    """Gracefully disconnects and deactivates the WLAN interface."""
    if wlan:
        wlan.disconnect()
        wlan.active(False)
        print("[WiFi] Disconnected.")


def sync_clock():
    """
    Synchronizes the Pico W system time with an NTP server.
    Returns True on success, False on failure.
    """
    try:
        print("[Time] Syncing with NTP...")
        ntptime.settime()
        t = time.localtime()
        print(
            f"[Time] Synced: {t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
        )
        return True
    except Exception as e:
        print(f"[Time] Sync failed: {e}")
        return False


# --- API Fetching Helpers ---


def _fetch_json(url, label="API"):
    """
    Generic function to fetch JSON data.
    Handles connection, status codes, and parsing.
    Returns parsed dict or None.
    """
    try:
        print(f"[{label}] Fetching: {url}")
        response = urequests.get(url, timeout=10)  # 10s timeout per request

        if response.status_code == 200:
            data = response.json()
            response.close()
            return data
        else:
            print(f"[{label}] Error: Status {response.status_code}")
            response.close()
            return None
    except Exception as e:
        print(f"[{label}] Request failed: {e}")
        return None


# --- Specific Data Fetchers ---


def get_weather_data():
    """
    Fetches current weather data from OpenWeatherMap OneCall API.
    Returns dict or None.
    """
    # Using the OneCall 3.0 endpoint (requires subscription, but assuming you have it)
    # Excluding minutely, hourly, daily, alerts to save bandwidth
    url = (
        f"https://api.openweathermap.org/data/3.0/onecall?"
        f"lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}"
        f"&units=imperial&exclude=minutely,hourly,daily,alerts"
    )
    return _fetch_json(url, "Weather")


def get_aqi_data():
    """
    Fetches Air Quality Index data from WAQI (World Air Quality Index).
    Returns dict or None.
    """
    # Fetching by City ID
    url = f"https://api.waqi.info/feed/@{AQICN_CITY_ID}/?token={AQICN_API_KEY}"
    return _fetch_json(url, "AQI")


def fetch_all_data():
    """
    Orchestrates fetching both weather and AQI data.
    Returns a tuple: (weather_data, aqi_data)
    """
    weather = get_weather_data()
    aqi = get_aqi_data()
    return weather, aqi
