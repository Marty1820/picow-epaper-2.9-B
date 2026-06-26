# Generica HTTP client for MicroPython

import requests


def fetch_json(url, params=None, timeout=10):
    """
    Fetches JSON data from a URL.

    Args:
        url (str): The URL to fetch
        timeout (int): Request timeout in seconds

    Returns:
        dict or None: Parsed JSON data on success, None on failure
    """
    try:
        if params:
            query_parts = []
            for k, v in params.items():
                if isinstance(v, list):
                    v = ",".join(str(item) for item in v)
                query_parts.append(f"{k}={v}")
            query_string = "&".join(query_parts)
            full_url = f"{url}?{query_string}"
        else:
            full_url = url

        print(f"[API] Fetching: {full_url}")
        response = requests.get(full_url, timeout=timeout)

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
        print(f"[API] Fetching: {url}")
        response = requests.get(url, timeout=timeout)

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
