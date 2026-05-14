# Entry point for the Weather/AQI Station
# Orchestrates network, data fetching, and display logic

import utime
import sys
from config import UPDATE_INTERVAL_SECONDS, RETRY_DELAY_SECONDS, OFFSET_HOURS
from network_api import connect_wifi, disconnect_wifi, sync_clock, fetch_all_data
from display_driver import EPD_2in9_B


def log_error(msg):
    """Simple error logger for Micropython."""
    print(f"ERROR: {msg}")


def main_loop():
    print("=== Weather Station Starting ===")

    while True:
        try:
            # 1. Network Connection
            wlan = connect_wifi()
            if not wlan:
                print("No WiFi. Retrying in 60s...")
                utime.sleep(RETRY_DELAY_SECONDS)
                continue

            # 2. Time Synchronization
            if not sync_clock():
                print(
                    "Time sync failed. Proceeding with system time (may be inaccurate)."
                )

            # 3. Fetch Data
            print("Fetching data...")
            weather_data, aqi_data = fetch_all_data()

            if not weather_data or not aqi_data:
                print(
                    "Warning: Failed to fetch one or both datasets. Skipping display update."
                )
                # Optional: Display an error message on screen here if desired
                utime.sleep(UPDATE_INTERVAL_SECONDS)
                continue

            # 4. Initialize Display & Render
            print("Initializing display...")
            epd = EPD_2in9_B()

            epd.render_full_screen(weather_data, aqi_data, OFFSET_HOURS)

            # 5. Sleep
            epd.sleep()
            disconnect_wifi(wlan)  # Save power by turning off radio

            print(f"Sleeping for {UPDATE_INTERVAL_SECONDS} seconds...")
            utime.sleep(UPDATE_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            print("\nInterrupted by user. Shutting down gracefully.")
            try:
                if "epd" in locals():
                    epd.sleep()
            except Exception:
                pass
            sys.exit(0)
        except Exception as e:
            log_error(f"Critical Error: {e}")

            # Attempt to recover
            print("Attempting recovery in 60s...")
            try:
                # Try to put display to sleep if it was initialized
                if "epd" in locals():
                    epd.sleep()
            except Exception:
                pass

            utime.sleep(RETRY_DELAY_SECONDS)


if __name__ == "__main__":
    main_loop()
