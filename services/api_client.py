# Generica HTTP client for MicroPython

import urequests


def fetch_json(url, timeout=10):
    """
    Fetches JSON data from a URL.

    Args:
        url (str): The URL to fetch
        timeout (int): Request timeout in seconds

    Returns:
        dict or None: Parsed JSON data on success, None on failure
    """
    try:
        print(f"[[API] Fetching: {url}")
        response = urequests.get(url, timeout=timeout)

        if response.status_code == 200:
            data = response.json()
            response.close()
            return data
        else:
            print(f"[API] Error: Status {response.status_code}")
            response.close()
            return None
    except Exception as e:
        print(f"[API] Request failed: {e}")
        return None


def fetch_text(url, timeout=10):
    """
    Fetches plain text from a URL.

    Args:
        url (str): The URL to fetch
        timeout (int): Request timeout in seconds

    Returns:
        dict or None: Parsed JSON data on success, None on failure
    """
    try:
        print(f"[[API] Fetching: {url}")
        response = urequests.get(url, timeout=timeout)

        if response.status_code == 200:
            text = response.text
            response.close()
            return text
        else:
            print(f"[API] Error: Status {response.status_code}")
            response.close()
            return None
    except Exception as e:
        print(f"[API] Request failed: {e}")
        return None
