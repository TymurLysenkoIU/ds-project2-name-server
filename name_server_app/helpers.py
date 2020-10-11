import requests

from name_server_proj.settings import REQUEST_TIMEOUT


def get_client_ip(request):
    """Return IP of request sender"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def ping(host: str):
    """Check if the specified host is available"""
    try:
        return requests.get(f'http://{host}/ping', timeout=REQUEST_TIMEOUT).status_code == 200
    except requests.RequestException:
        return False
