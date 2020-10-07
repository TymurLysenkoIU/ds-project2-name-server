from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from urllib import parse
from .parse_request import parse

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
            return HttpResponse(answer, enctype="multipart/form-data",
                                status=200)

    elif request.method == 'POST':
        print(request)
        url = request.get_full_path()
        args = dict(parse.parse_qsl(parse.urlsplit(url).query))
        pyDict = {int(key): args[key] for key in args}
        array = [0 for i in range(len(pyDict))]
        for key, val in pyDict.items():
            array[key] = val
        file = request.FILES['file'].read()
        answer = parse(array, file)
        return HttpResponse(str(answer), status=200)
