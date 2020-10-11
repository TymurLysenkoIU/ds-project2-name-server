from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from urllib import parse as urlparse
import logging
import sys

from .parse_request import parse
from .distributed_file_system import Storage
from .helpers import get_client_ip

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG, format='%(levelname)s: %(message)s')

@csrf_exempt
def send_request(request):
    """
    List all code snippets, or create a new snippet.
    """

    if request.method == 'GET':
        pyDict = dict(request.GET.lists())
        pyDict = {int(key):pyDict[key][0] for key in pyDict}
        array = [0 for i in range(len(pyDict))]
        for key, val in pyDict.items():
            array[key] = val
        answer = parse(array)
        if pyDict[0] != 'read':
            return HttpResponse(str(answer), status=200)
        else:
            return HttpResponse(answer,
                                status=200)

    elif request.method == 'POST':
        print(request)
        url = request.get_full_path()
        print(url)
        args = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
        print(args)
        pyDict = {int(key): args[key] for key in args}
        array = [0 for i in range(len(pyDict))]
        for key, val in pyDict.items():
            array[key] = val
        print(array)
        file = request.FILES['file']
        answer = parse(array, file)
        return HttpResponse(str(answer), status=200)


def connect_storage_server(request):
    ip = get_client_ip(request)
    storage = Storage()
    storage.add_storage_server(ip)
    logging.info(f'A new storage server has been added: {ip}')
    return HttpResponse(status=202)
