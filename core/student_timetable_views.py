from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .helpers import set_config
from .models import Staff
from .timetable_models import StaffTimeTable
from .models import SemesterSubject
from datetime import datetime

@login_required
def student_timetable(request):
    context = set_config(request)
    # Get the student's advisor or class staff
    staff = None
    if hasattr(context['duser'], 'advisor') and context['duser'].advisor:
        staff = context['duser'].advisor
    elif hasattr(context['duser'], 'mentor') and context['duser'].mentor:
        staff = context['duser'].mentor
    # Define days and periods (should match staff timetable)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = ['1', '2', '3', '4', '5', '6', '7']
    table = {}
    if staff:
        try:
            timetable_obj = StaffTimeTable.objects.get(staff=staff)
            table = timetable_obj.data.copy() if timetable_obj.data else {}
            # Map subject IDs to names
            for k, v in table.items():
                if v and str(v).isdigit():
                    try:
                        subject = SemesterSubject.objects.get(id=v)
                        table[k] = subject.name
                    except SemesterSubject.DoesNotExist:
                        pass
        except StaffTimeTable.DoesNotExist:
            pass
    context['days'] = days
    context['periods'] = periods
    context['table'] = table
    context['staff'] = staff
    # Handle day selection via GET parameter
    # Accepts 'All' or one of the days; default is today's weekday if available
    day_param = request.GET.get('day')
    # determine default day as current weekday name (Monday..Friday)
    today_name = datetime.now().strftime('%A')
    if day_param:
        selected_day = day_param if day_param == 'All' or day_param in days else None
    else:
        # default to today if weekday in our list, else 'All'
        selected_day = today_name if today_name in days else 'All'

    if selected_day == 'All' or not selected_day:
        days_to_show = days
    else:
        days_to_show = [selected_day]

    context['selected_day'] = selected_day
    context['days_to_show'] = days_to_show
    # Debug info
    context['debug_user'] = str(request.user)
    context['debug_duser'] = str(context.get('duser'))
    return render(request, 'student/timetable.html', context)
