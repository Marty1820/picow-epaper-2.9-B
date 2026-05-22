# Generic WiFi and Time Synchronization module for micropython

import network
import ntptime
import time
import utime


# --- WiFi Management ---
def connect_wifi(ssid, password, timeout=30):
    """
    Connects to the configured Wi-Fi network.

    Args:
        ssid (str): Network name
        password (str): Network password
        timeout (int): Connection timeout in seconds

    Returns:
        network.WLAN: WLAN object if successful, None otherwise.
    """
    print(f"[WiFi] Connecting to {ssid}...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        ip = wlan.ifconfig()[0]
        print(f"[WiFi] Already connected. IP: {ip}")
        return wlan

    wlan.connect(ssid, password)

    start_time = utime.time()
    while not wlan.isconnected():
        if utime.time() - start_time > timeout:
            print("[WiFi] Connection timed out.")
            return None

        utime.sleep(1)

    ip = wlan.ifconfig()[0]
    print(f"[WiFi] Connected! IP: {ip}")
    return wlan


def disconnect_wifi(wlan):
    """
    Gracefully disconnects and deactivates the WLAN interface.

    Args:
        wlan (network.WLAN): The WLAN object to disconnect
    """
    if wlan:
        wlan.disconnect()
        wlan.active(False)
        print("[WiFi] Disconnected.")


def sync_clock():
    """
    Synchronizes the system time with an NTP server.
    Returns:
        bool: True on success, False on failure.
    """
    try:
        print("[Time] Syncing with NTP...")
        ntptime.settime()
        t = time.localtime()
        print(
            f"[Time] Synced: {t[0]}-{t[1]:02d}-{t[2]:02d} "
            f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d}"
        )
        return True
    except Exception as e:
        print(f"[Time] Sync failed: {e}")
        return False


def get_local_time(offset_hours=0):
    """
    Gets the current local time with timezone offset.

    Args:
        offset_hours (int): Hours offset from UTC

    Returns:
        tuple: (date_string, time_string) formatted as YYYY-MM-DD and HH:MM
    """
    try:
        t = time.localtime()
        utc_seconds = time.mktime(t)
        local_seconds = utc_seconds + (offset_hours * 3600)
        local_t = time.localtime(local_seconds)

        daystamp = f"{local_t[0]}-{local_t[1]:02d}-{local_t[2]:02d}"
        timestamp = f"{local_t[3]:02d}:{local_t[4]:02d}"

        return daystamp, timestamp
    except Exception as e:
        print(f"[Time] Get local time failed: {e}")
        return "Unknown", "Unknown"
