# Entry point for the Weather/AQI Station
# Orchestrates network, data fetching, and display logic

import utime
from config import (
    UPDATE_INTERVAL_SECONDS,
    RETRY_DELAY_SECONDS,
    OFFSET_HOURS,
    THRESHOLDS,
    TOTAL_AQI_THRESHOLD,
    SSID,
    PASSWORD,
)
from hardware.network import connect_wifi, disconnect_wifi, sync_clock, get_local_time
from services.weather_service import (
    fetch_all_data,
    format_weather_display,
    format_aqi_display,
)
from hardware.display import EPD_2in9_B


def log_error(msg):
    """Simple error logger for Micropython."""
    print(f"ERROR: {msg}")


def render_display(epd, weather_data, aqi_data, offset_hours):
    """
    Renders weather and AQI data to the e-paper display.

    Args:
        epd: Display driver instance
        weather_data: Formatted weather data dict
        aqi_data: Formatted AQI data dict
        offset_hours: UTC offset for local time
    """
    # Clear buffers
    epd.imageblack.fill(0xFF)
    epd.imagered.fill(0xFF)

    # --- Header ---
    epd.draw_text_black("WEATHER STATION", 5, 10)

    # --- Weather Section ---
    if weather_data:
        epd.draw_text_black(weather_data["desc"][:18], 5, 25)
        epd.draw_text_black(f"TEMP  : {int(weather_data['temp'])}F", 5, 40)
        epd.draw_text_black(f"FEELS : {int(weather_data['feels_like'])}F", 5, 55)
        epd.draw_text_black(f"HUMID : {weather_data['humidity']}%", 5, 70)
        epd.draw_text_black(f"WIND  : {round(weather_data['wind_speed'])}mph", 5, 85)
    else:
        epd.draw_text_black("Weather Error", 5, 25)

    # --- AQI Section ---
    epd.draw_text_black("AIR QUALITY", 5, 115)

    if aqi_data:
        # Draw total AQI
        total_aqi = aqi_data["total_aqi"]
        is_high = total_aqi >= TOTAL_AQI_THRESHOLD
        epd.clear_area(10, 130, 60, 12)
        epd.draw_text_conditional(f"AQI    : {total_aqi}", 10, 130, is_high)

        # Draw individual pollutants
        y_offset = 145
        iaqi = aqi_data.get("iaqi", {})

        for key, cfg in THRESHOLDS.items():
            val_data = iaqi.get(key)
            value = None
            if val_data:
                value = val_data.get("v") if isinstance(val_data, dict) else val_data

            if value is None:
                text = cfg["label"] + "N/A"
                is_high = False
            else:
                text = (
                    f"{cfg['label']}{value:.1f}"
                    if isinstance(value, float)
                    else f"{cfg['label']}{int(value)}"
                )
                is_high = value >= cfg["threshold"]

            epd.clear_area(10, y_offset, 60, 12)
            epd.draw_text_conditional(text, 10, y_offset, is_high)
            y_offset += 15
    else:
        epd.draw_text_black("AQI Error", 5, 115)

    # --- Timestamp ---
    daystamp, timestamp = get_local_time(offset_hours)
    epd.draw_text_black("Last Update:", 10, 255)
    epd.draw_text_black(daystamp, 10, 270)
    epd.draw_text_black(timestamp, 10, 285)

    # Refresh display
    epd.render()
    print("[MAIN] Render complete")


def main_loop():
    """Main application loop."""
    print("=== Weather Station Starting ===")

    while True:
        try:
            # 1. Network Connection
            wlan = connect_wifi(SSID, PASSWORD)
            if not wlan:
                print("[MAIN] No Wi-Fi. Retrying in 60s...")
                utime.sleep(RETRY_DELAY_SECONDS)
                continue

            # 2. Time Synchronization
            if not sync_clock():
                print("[MAIN] Time sync failed using system time.")

            # 3. Fetch Data
            print("[MAIN] Fetching data...")
            weather_raw, aqi_raw = fetch_all_data()

            if not weather_raw or not aqi_raw:
                print("[WARN] Failed to fetch data skipping display update.")
                utime.sleep(UPDATE_INTERVAL_SECONDS)
                continue

            # 4. Format Data
            weather_data = format_weather_display(weather_raw)
            aqi_data = format_aqi_display(aqi_raw)

            # 5. Initialize Display & Render
            print("[MAIN] Init display")
            epd = EPD_2in9_B()
            render_display(epd, weather_data, aqi_data, OFFSET_HOURS)

            # 6. Sleep
            epd.sleep()
            disconnect_wifi(wlan)  # Save power by turning off radio

            print(f"[MAIN] Sleeping {UPDATE_INTERVAL_SECONDS} secs")
            utime.sleep(UPDATE_INTERVAL_SECONDS)

        except Exception as e:
            log_error(f"Critical Error: {e}")

            # Attempt to recover
            print(f"[MAIN] Attempt recovery in {RETRY_DELAY_SECONDS}secs")
            try:
                # Try to put display to sleep if it was initialized
                if "epd" in locals():
                    epd.sleep()
            except Exception:
                pass

            utime.sleep(RETRY_DELAY_SECONDS)


if __name__ == "__main__":
    main_loop()
