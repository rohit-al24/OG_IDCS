
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Staff, Student
from .helpers import set_config

@login_required
def staff_profile(request):
    context = set_config(request)
    staff = context.get('duser')
    dept_ahod = None
    dept_hod = None
    if hasattr(staff, 'department') and staff.department is not None:
        from .models import AHOD, HOD
        dept_ahod = AHOD.objects.filter(department=staff.department).first()
        dept_hod = HOD.objects.filter(department=staff.department).first()
    context['dept_ahod'] = dept_ahod
    context['dept_hod'] = dept_hod
    return render(request, 'common/profile.html', context)

@login_required
def hod_profile(request):
    context = set_config(request)
    # Find AHOD for this HOD's department
    hod_staff = context.get('duser')
    dept_ahod = None
    dept_hod = None
    if hasattr(hod_staff, 'department') and hod_staff.department is not None:
        from .models import AHOD, HOD
        dept_ahod = AHOD.objects.filter(department=hod_staff.department).first()
        dept_hod = HOD.objects.filter(department=hod_staff.department).first()
    context['dept_ahod'] = dept_ahod
    context['dept_hod'] = dept_hod
    return render(request, 'common/profile.html', context)
