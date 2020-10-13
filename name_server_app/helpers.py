import requests

from name_server_proj.settings import REQUEST_TIMEOUT, STORAGE_SERVER_PORT


def get_client_ip(request) -> str:
    """Return IP of request sender"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def ping(host: str, port=STORAGE_SERVER_PORT) -> bool:
    """Check if the specified host is available"""
    try:
        return requests.get(f'http://{host}:{port}/ping', timeout=REQUEST_TIMEOUT).status_code == 200
    except requests.RequestException:
        return False


def request_space_available(host: str, port=STORAGE_SERVER_PORT) -> int:
    """Return how many bytes are available at storage directory."""
    try:
        return requests.get(f'http://{host}:{port}/info/space', timeout=REQUEST_TIMEOUT).json()['bytes_available']
    except Exception:
        return 0
