from django.shortcuts import render, get_object_or_404
from .models import Staff, Student
from django.contrib.auth.decorators import login_required

@login_required

def my_mentees(request):
    staff = get_object_or_404(Staff, user=request.user)
    mentees = Student.objects.filter(mentor=staff).order_by('name')
    return render(request, 'hod/mentees_list.html', {'staff': staff, 'mentees': mentees, 'duser': staff})

@login_required
def view_mentees(request, staff_id=None, self_view=False):
    if self_view or staff_id is None:
        staff = get_object_or_404(Staff, user=request.user)
    else:
        staff = get_object_or_404(Staff, id=staff_id)
    mentees = Student.objects.filter(mentor=staff).order_by('name')
    logged_in_staff = get_object_or_404(Staff, user=request.user)
    return render(request, 'hod/mentees_list.html', {
        'staff': staff,
        'mentees': mentees,
        'duser': logged_in_staff
    })

