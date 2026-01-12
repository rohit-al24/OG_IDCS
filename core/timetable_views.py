from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .helpers import set_config
from .timetable_models import StaffTimeTable
from django.http import JsonResponse
from .models import SemesterSubject, Department, Semester
import logging

logger = logging.getLogger(__name__)

@login_required
def staff_timetable(request):
    context = set_config(request)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = ['1', '2', '3', '4', '5', '6', '7']
    staff = context['duser']
    table = {}
    my_table = {}
    try:
        timetable_obj = StaffTimeTable.objects.get(staff=staff)
        table = timetable_obj.data
        my_table = timetable_obj.my_timetable_data
    except StaffTimeTable.DoesNotExist:
        timetable_obj = None
    if request.method == 'POST':
        # Determine which form was submitted
        if 'my-edit-btn' in request.POST or 'my-save-btn' in request.POST or any(k.startswith('my_') for k in request.POST.keys()):
            # My Timetable form
            for day in days:
                for period in periods:
                    key = f"{day}_{period}"
                    my_key = f"my_subject_{key}"
                    my_table[key] = request.POST.get(my_key, '')
            StaffTimeTable.objects.update_or_create(staff=staff, defaults={'my_timetable_data': my_table, 'data': table})
            context['my_message'] = 'My Timetable updated!'
        else:
            # Main timetable form
            for day in days:
                for period in periods:
                    key = f"{day}_{period}"
                    subject_key = f"subject_{key}"
                    selected_subject = request.POST.get(subject_key, '')
                    if selected_subject and selected_subject != 'others':
                        table[key] = selected_subject
                    else:
                        table[key] = ''
            StaffTimeTable.objects.update_or_create(staff=staff, defaults={'data': table, 'my_timetable_data': my_table})
            context['message'] = 'Timetable updated!'
    # Get department subjects for dropdown
    department = getattr(staff, 'department', None)
    department_subjects = []
    if department:
        semesters = Semester.objects.filter(department=department)
        department_subjects = SemesterSubject.objects.filter(semester__in=semesters)
    # Add 'Others' option to department_subjects
    department_subjects = list(department_subjects)  # Ensure it's mutable
    # Correctly handle 'Others' option
    department_subjects = [{'id': subject.id, 'name': subject.name} for subject in department_subjects]  # Convert to list of dictionaries
    department_subjects = [subject for subject in department_subjects if subject['name'] != 'Others']  # Remove duplicate 'Others'
    department_subjects.append({'id': 'others', 'name': 'Others'})



    # Fetch other department subjects for 'Others' option
    other_department_subjects = SemesterSubject.objects.exclude(semester__department=department)
    context['other_department_subjects'] = [{'id': subject.id, 'name': subject.name} for subject in other_department_subjects]

    # Fetch all departments for the department dropdown
    all_departments = Department.objects.all()
    context['all_departments'] = [{'id': dept.id, 'name': dept.name} for dept in all_departments]

    # all_subjects should include all subjects from all departments for correct restoration
    all_subjects = list(SemesterSubject.objects.all())
    all_subjects = [{'id': subject.id, 'name': subject.name} for subject in all_subjects]
    all_subjects = [subject for subject in all_subjects if subject['name'] != 'Others']
    all_subjects.append({'id': 'others', 'name': 'Others'})
    context['all_subjects'] = all_subjects
    context['days'] = days
    context['periods'] = periods
    context['table'] = table
    context['my_table'] = my_table
    return render(request, 'staff/timetable.html', context)

@login_required
def hod_timetable(request):
    context = set_config(request)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    periods = ['1', '2', '3', '4', '5', '6', '7']
    hod = context['duser']
    table = {}
    my_table = {}
    try:
        timetable_obj = StaffTimeTable.objects.get(staff=hod)
        table = timetable_obj.data
        my_table = timetable_obj.my_timetable_data
    except StaffTimeTable.DoesNotExist:
        timetable_obj = None

    # Get department subjects for dropdown
    department = getattr(hod, 'department', None)
    department_subjects = []
    if department:
        semesters = Semester.objects.filter(department=department)
        department_subjects = SemesterSubject.objects.filter(semester__in=semesters)
    # Add 'Others' option to department_subjects
    department_subjects = list(department_subjects)  # Ensure it's mutable
    department_subjects = [{'id': subject.id, 'name': subject.name} for subject in department_subjects]  # Convert to list of dictionaries
    department_subjects = [subject for subject in department_subjects if subject['id'] != 'others']  # Remove duplicate 'Others'
    # Add 'Others' option to department_subjects if not already present
    if not any(subject['id'] == 'others' for subject in department_subjects):
        department_subjects.append({'id': 'others', 'name': 'Others'})

    if request.method == 'POST':
        # Handle 'Others' option for custom subject names
        for day in days:
            for period in periods:
                key = f"{day}_{period}"
                selected_subject = request.POST.get(key, '')
                if selected_subject == 'others':
                    custom_subject = request.POST.get(f"custom_{key}", '')
                    my_table[key] = custom_subject
                else:
                    my_table[key] = selected_subject

        StaffTimeTable.objects.update_or_create(staff=hod, defaults={'my_timetable_data': my_table, 'data': table})
        context['message'] = 'HOD Timetable updated!'

    context['all_subjects'] = department_subjects
    context['days'] = days
    context['periods'] = periods
    context['table'] = table
    context['my_table'] = my_table
    return render(request, 'hod/timetable.html', context)

@login_required
def get_department_subjects(request, department_id):
    subjects = SemesterSubject.objects.filter(semester__department_id=department_id)
    subject_list = [{'id': subject.id, 'name': subject.name} for subject in subjects]
    return JsonResponse({'subjects': subject_list})
