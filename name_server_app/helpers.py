import requests

from name_server_proj.settings import REQUEST_TIMEOUT, STORAGE_SERVER_PORT


def get_client_ip(request) -> str:
    """Return IP of request sender"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def ping(host: str) -> bool:
    """Check if the specified host is available"""
    try:
        return requests.get(f'http://{host}:{STORAGE_SERVER_PORT}/ping', timeout=REQUEST_TIMEOUT).status_code == 200
    except requests.RequestException:
        return False


def request_space_available(host: str) -> int:
    """Return how many bytes are available at storage directory."""
    try:
        return requests.get(f'http://{host}:{STORAGE_SERVER_PORT}/info/space', timeout=REQUEST_TIMEOUT).json()['bytes_available']
    except Exception:
        return 0


if __name__ == '__main__':
    host = '192.168.31.157'
    print(requests.get(f'http://{host}/info/space', timeout=REQUEST_TIMEOUT))
    print(requests.get(f'http://{host}/info/space', timeout=REQUEST_TIMEOUT).json())
    print(requests.get(f'http://{host}/info/space', timeout=REQUEST_TIMEOUT).json()['bytes_available'])