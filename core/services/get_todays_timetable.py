from django.utils import timezone
from core.timetable_models import StaffTimeTable
from core.models import SemesterSubject


def _lookup_subject_name(val):
    """Try to resolve a stored timetable value to a human-friendly subject name.

    The timetable JSON may store either a SemesterSubject id (as int or string)
    or a custom name. If it's an id and a matching SemesterSubject exists,
    return its name, otherwise return the original value (or empty string).
    """
    if not val:
        return ''
    # If it's already a string that looks like a name (non-numeric), return as-is
    try:
        sid = int(val)
    except Exception:
        return val
    try:
        subj = SemesterSubject.objects.get(id=sid)
        return subj.name
    except SemesterSubject.DoesNotExist:
        return str(val)


def get_todays_timetable(staff):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = ['1', '2', '3', '4', '5', '6', '7']
    today = timezone.now().strftime('%A')
    if today not in days:
        return None
    try:
        timetable_obj = StaffTimeTable.objects.get(staff=staff)
        table = timetable_obj.data
        my_table = timetable_obj.my_timetable_data
    except StaffTimeTable.DoesNotExist:
        return None
    # Get today's periods for both tables, resolving subject ids to names when possible
    today_periods = []
    for period in periods:
        key = f"{today}_{period}"
        subject = _lookup_subject_name(table.get(key, ''))
        my_subject = _lookup_subject_name(my_table.get(key, ''))
        today_periods.append({'period': period, 'subject': subject, 'my_subject': my_subject})
    return today_periods
