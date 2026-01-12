from django.http import JsonResponse
from .models import *


def send_hod_API(request,id):

    data = {
        'name':["Sriram","Muraga"],
        'ratings':[6.4,3.2]
    }

    return JsonResponse(data)

