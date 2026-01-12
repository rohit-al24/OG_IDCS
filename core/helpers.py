from .models import *
from django.contrib.auth.models import User

def set_config(request):
    context = {}
    if not request.user.is_authenticated:
        return context
    user = User.objects.get(username=request.user.username)
    if user.is_staff:
        context['duser'] = Staff.objects.get(user=request.user)
    else:
        context['duser'] = Student.objects.get(user=request.user)
        context['OD'] = OD.objects.filter(user=context['duser'].id)
        context['LE'] = LEAVE.objects.filter(user=context['duser'].id)
        context['GP'] = GATEPASS.objects.filter(user=context['duser'].id)
    return context

def get_post(request,val,**kwargs):
    return request.POST.get(val,**kwargs)


def map_feedback(staffs):
    ratings = {
    }

    for staff in staffs:
        my_feedback = staff.my_feedbacks.all()
        if len(my_feedback)==0:
            continue
        points = 0
        for j in my_feedback:
            points +=j.avg()
        
        avg = points/len(my_feedback)
        ratings[staff.name] = [round(avg),len(my_feedback)]
        
    
    return ratings