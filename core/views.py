from django.contrib.auth.decorators import login_required, user_passes_test

from collections import defaultdict
from django.contrib import messages
from django.shortcuts import redirect, render, HttpResponse
from django.http import JsonResponse
from .models import SportsOD, SportsODPlayer, Student, Staff, Notification, CertificateUpload
from django.db import transaction
from django.views.decorators.http import require_GET
from .forms import CertificateUploadForm
from .models import Attendance
from django.utils import timezone

def is_advisor(user):
    return hasattr(user, 'staff') and (getattr(user.staff, 'position', None) == 4 or getattr(user.staff, 'position2', None) == 4)

def is_staff_member(user):
    """Check if user is a staff member (any position)"""
    return hasattr(user, 'staff')

@login_required
def advisor_student_od_status(request, student_id):
    # Check if staff has relationship with this student
    if not hasattr(request.user, 'staff'):
        return redirect('/login/')
    
    staff = request.user.staff
    student = Student.objects.get(id=student_id)
    
    # Check if staff is related to this student (advisor, mentor, or teaching staff)
    from django.db.models import Q
    is_related = Student.objects.filter(
        Q(id=student_id) & (Q(advisor=staff) | Q(a_advisor=staff) | Q(mentor=staff) | Q(teaching_staffs=staff))
    ).exists()
    
    if not is_related:
        messages.error(request, "You don't have permission to view this student's records.")
        return redirect('student_details')
    
    context = set_config(request)
    from .models import OD
    od_records = OD.objects.filter(user=student)
    context['od_records'] = od_records
    context['student'] = student
    return render(request, 'staff/od_status.html', context)

@login_required
def advisor_student_leave_status(request, student_id):
    # Check if staff has relationship with this student
    if not hasattr(request.user, 'staff'):
        return redirect('/login/')
    
    staff = request.user.staff
    student = Student.objects.get(id=student_id)
    
    # Check if staff is related to this student (advisor, mentor, or teaching staff)
    from django.db.models import Q
    is_related = Student.objects.filter(
        Q(id=student_id) & (Q(advisor=staff) | Q(a_advisor=staff) | Q(mentor=staff) | Q(teaching_staffs=staff))
    ).exists()
    
    if not is_related:
        messages.error(request, "You don't have permission to view this student's records.")
        return redirect('student_details')
    
    context = set_config(request)
    from .models import LEAVE
    leave_records = LEAVE.objects.filter(user=student)
    context['leave_records'] = leave_records
    context['student'] = student
    return render(request, 'staff/leave_status.html', context)

@login_required
def advisor_student_gatepass_status(request, student_id):
    # Check if staff has relationship with this student
    if not hasattr(request.user, 'staff'):
        return redirect('/login/')
    
    staff = request.user.staff
    student = Student.objects.get(id=student_id)
    
    # Check if staff is related to this student (advisor, mentor, or teaching staff)
    from django.db.models import Q
    is_related = Student.objects.filter(
        Q(id=student_id) & (Q(advisor=staff) | Q(a_advisor=staff) | Q(mentor=staff) | Q(teaching_staffs=staff))
    ).exists()
    
    if not is_related:
        messages.error(request, "You don't have permission to view this student's records.")
        return redirect('student_details')
    
    context = set_config(request)
    from .models import GATEPASS
    gatepass_records = GATEPASS.objects.filter(user=student)
    context['gatepass_records'] = gatepass_records
    context['student'] = student
    return render(request, 'staff/gatepass_status.html', context)

@login_required
@login_required
def advisor_student_bonafide_status(request, student_id):
    # Check if staff has relationship with this student
    if not hasattr(request.user, 'staff'):
        return redirect('/login/')
    
    staff = request.user.staff
    student = Student.objects.get(id=student_id)
    
    # Check if staff is related to this student (advisor, mentor, or teaching staff)
    from django.db.models import Q
    is_related = Student.objects.filter(
        Q(id=student_id) & (Q(advisor=staff) | Q(a_advisor=staff) | Q(mentor=staff) | Q(teaching_staffs=staff))
    ).exists()
    
    if not is_related:
        messages.error(request, "You don't have permission to view this student's records.")
        return redirect('student_details')
    
    context = set_config(request)
    from .models import BONAFIDE
    bonafide_records = BONAFIDE.objects.filter(user=student)
    context['bonafide_records'] = bonafide_records
    context['student'] = student
    return render(request, 'staff/bonafide_status.html', context)

from django.contrib.auth import get_user_model
from feed360.models import FeedbackQuestion
from django.contrib.auth.decorators import user_passes_test
import random
from django.core.mail import send_mail
from django.conf import settings
from .models import BONAFIDE, GATEPASS, Staff, AHOD, HOD, Notification
from .models import SemesterSubject
from django.db import models
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import *
from .helpers import *
from .constants import *
from django.contrib.messages import error, success, warning
from io import BytesIO
from django.core.files import File
from django.utils.dateparse import parse_datetime   # ✅ must be here
import qrcode

def home(request):
    # Provide recent published notices with images for the homepage hero carousel
    from .models import Notice
    # Temporary guard: if migrations haven't been applied or the table is missing
    # return an empty queryset instead of raising a 500. Long-term fix: run
    # `manage.py migrate` (or use a proper Postgres DB in production).
    from django.db.utils import OperationalError
    try:
        notices = Notice.objects.filter(published=True).exclude(image__isnull=True).exclude(image__exact='').order_by('-publish_date', '-created')[:12]
    except OperationalError:
        # Database tables not ready (e.g. during first deploy). Show no notices.
        # Use a plain list instead of an empty QuerySet so template boolean
        # checks (``{% if notices %}``) won't trigger a DB query and raise
        # OperationalError when the table is missing.
        notices = []
    return render(request, 'home.html', {'notices': notices})

def is_hod(user):
    return user.is_staff and hasattr(user, 'staff') and user.staff.position == 0

@login_required
def scan_gatepass_qr(request):
    from django.utils import timezone
    context = set_config(request)
    student = context.get('duser')
    message = ""
    error = ""

    # Find an approved gate pass for today that hasn't been fully used
    today = timezone.now().date()
    active_gatepass = GATEPASS.objects.filter(
        user=student,
        Hstatus='Approved',
        start__date__lte=today,
        end__date__gte=today
    ).order_by('-created').first()

    if not active_gatepass:
        error = "You do not have an approved gate pass for today."
    else:
        # Check if this is an exit or an entry scan
        if not active_gatepass.exit_time:
            active_gatepass.exit_time = timezone.now()
            message = f"Exit successful at {active_gatepass.exit_time.strftime('%I:%M %p')}. You are now out of campus."
        elif not active_gatepass.entry_time:
            scan_time = timezone.now()
            active_gatepass.entry_time = scan_time
            message = f"Entry successful at {scan_time.strftime('%I:%M %p')}. Welcome back to campus."
        else:
            error = "This gate pass has already been used for both exit and entry."
        if not error:
            active_gatepass.save()

    context['message'] = message
    context['error'] = error
    # This new template will simply show the success/error message
    return render(request, 'student/scan_result.html', context)
@user_passes_test(is_hod)
def hod_sports_od_view(request):
    context = set_config(request)
    hod_staff = Staff.objects.get(user=request.user)
    # Get all players from the HOD's department
    players = SportsODPlayer.objects.filter(
        student__department=hod_staff.department
    ).select_related('student', 'sports_od__created_by').order_by('-sports_od__created_at')

    # Group players by event
    players_by_event = defaultdict(list)
    for player in players:
        players_by_event[player.sports_od].append(player)

    context['players_by_event'] = dict(players_by_event)
    return render(request, 'hod/sports_od_approval.html', context)


@login_required
@user_passes_test(is_hod)
def hod_sports_od_action(request, player_id):
    if request.method == 'POST':
        player = SportsODPlayer.objects.get(id=player_id)
        action = request.POST.get('action') # 'Approved' or 'Rejected'
        remark = request.POST.get('hod_remark')

        # Security check: ensure HOD is acting on a student from their department
        hod_staff = Staff.objects.get(user=request.user)
        if player.student.department == hod_staff.department:
            player.status = action
            player.hod_remark = remark
            player.save()

            # Notify the PET staff
            Notification.objects.create(
                staff=player.sports_od.created_by,
                message=f"Sports OD for {player.student.name} ({player.sports_od.event_name}) has been {action.lower()} by HOD."
            )
            messages.success(request, f"Action '{action}' recorded for {player.student.name}.")
        else:
            messages.error(request, "You are not authorized to perform this action.")

    return redirect('hod_sports_od_view')

# Helper function to check if a user is a PET Staff
def is_pet_staff(user):
    return (
        user.is_staff and hasattr(user, 'staff') and (
            getattr(user.staff, 'position', None) == 5 or
            getattr(user.staff, 'position2', None) == 5 or
            getattr(user.staff, 'position3', None) == 5
        )
    )

@login_required
@user_passes_test(is_pet_staff, login_url='/dash/')
def pet_dashboard(request):
    context = set_config(request)
    return render(request, 'pet/dash.html', context)

@login_required
@user_passes_test(is_pet_staff, login_url='/dash/')
@transaction.atomic
def pet_sports_od_apply(request):
    context = set_config(request)
    if request.method == 'POST':
        event_name = request.POST.get('event_name')
        body = request.POST.get('body') # Get the new body field
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        student_rolls = request.POST.getlist('student_roll')

        pet_staff = Staff.objects.get(user=request.user)
        # Create the main SportsOD event
        sports_od = SportsOD.objects.create(
            event_name=event_name,
            body=body, # Save the new body field
            start_date=start_date,
            end_date=end_date,
            created_by=pet_staff
        )

        # Find students by user__username (the long ID) instead of roll
        students_found = Student.objects.filter(user__username__in=student_rolls)
        hods_to_notify = set()

        for student in students_found:
            SportsODPlayer.objects.create(sports_od=sports_od, student=student)
            if student.hod:
                hods_to_notify.add(student.hod)

        # Notify the relevant HODs
        for hod in hods_to_notify:
            Notification.objects.create(
                staff=hod,
                role='hod',
                message=f"New Sports OD approval request for '{event_name}' needs your attention."
            )

        messages.success(request, 'Sports OD application submitted successfully!')
        return redirect('pet_sports_od_status')

    return render(request, 'pet/sports_od_apply.html', context)

@login_required
@user_passes_test(is_pet_staff, login_url='/dash/')
def pet_sports_od_status(request):
    context = set_config(request)
    pet_staff = Staff.objects.get(user=request.user)
    context['sports_ods'] = SportsOD.objects.filter(created_by=pet_staff).prefetch_related('players__student__department')
    return render(request, 'pet/sports_od_status.html', context)

# ...existing code...

@login_required
def get_student_details(request, user_id): # Changed parameter name
    """
    API endpoint to fetch student details by user_id (username).
    """
    try:
        # Changed query to search by user__username
        student = Student.objects.get(user__username=user_id)
        data = {
            'exists': True,
            'name': student.name,
            'department': student.department.name if student.department else 'N/A', # Changed .code to .name
            'year': student.year,
        }
    except Student.DoesNotExist:
        data = {'exists': False, 'error': 'Student not found.'}
    return JsonResponse(data)


@login_required
def gatepass_scanner_view(request):
    """Render the gatepass scanner page with the usual context (duser/profile).

    This replaces the previous lambda-based URL that rendered the template without
    adding the standard context, which caused the profile name/image to be empty.
    """
    context = set_config(request)
    return render(request, 'student/gatepass_scanner.html', context)

# Staff view: show certificates uploaded by their mentees/advisees
@login_required

@login_required
def staff_certificates(request):
    # Use set_config to get the correct user context (including HOD status)
    context = set_config(request)
    staff = context.get('duser')

    if not staff:
        messages.error(request, "Staff profile not found.")
        return redirect('dash')

    # Students where this staff is mentor or advisor
    mentees = Student.objects.filter(mentor=staff)
    advisees = Student.objects.filter(advisor=staff)
    # Certificates from both groups
    certificates = CertificateUpload.objects.filter(student__in=mentees | advisees).order_by('-uploaded_at')
    # Add the certificates to the context and render
    context['certificates'] = certificates
    return render(request, 'staff/certificates.html', context)

# Student certificate upload view
@login_required
def certificate_upload_view(request):
    context = set_config(request)
    student = context.get('duser')
    if not student:
        messages.error(request, "Student profile not found.")
        return redirect('dash')
    if request.method == 'POST':
        form = CertificateUploadForm(request.POST, request.FILES)
        if form.is_valid():
            cert = form.save(commit=False)
            cert.student = student
            cert.save()
            messages.success(request, "Certificate uploaded successfully!")
            return redirect('certificate_upload')
    else:
        form = CertificateUploadForm()
    # Show previous uploads for this student
    uploads = CertificateUpload.objects.filter(student=student).order_by('-uploaded_at')
    context['form'] = form
    context['uploads'] = uploads
    return render(request, 'student/certificate_upload.html', context)

# API endpoint for recent notifications (for live refresh)
@login_required
@require_GET
def recent_notifications_api(request):
    """
    Return recent notifications for the logged-in user.
    - If the user is a Student, return student notifications.
    - If the user is a Staff (including HOD/AHOD), return staff notifications. For HODs we prefer role='hod'.

    The client-side UI further limits display to the most recent 5, so here we return up to 10
    to give some headroom for badge calculation while keeping payload small.
    """
    notes_qs = None
    # Try student notifications first
    try:
        student = Student.objects.get(user=request.user)
        notes_qs = Notification.objects.filter(student=student).order_by('-created_at')[:10]
    except Student.DoesNotExist:
        # Not a student — try staff
        try:
            staff = Staff.objects.get(user=request.user)
            # If HOD, prefer hod-role notifications
            if getattr(staff, 'position', None) == 0:
                notes_qs = Notification.objects.filter(staff=staff, role__iexact='hod').order_by('-created_at')[:10]
            else:
                notes_qs = Notification.objects.filter(staff=staff).order_by('-created_at')[:10]
        except Staff.DoesNotExist:
            # Unknown user type — return empty
            return JsonResponse({'notifications': [], 'unread_count': 0})

    notifications = []
    unread_count = 0
    for note in notes_qs:
        is_read = bool(getattr(note, 'is_read', False))
        if not is_read:
            unread_count += 1
        notifications.append({
            'created_at': note.created_at.strftime('%d %b %Y %H:%M') if getattr(note, 'created_at', None) else '',
            'message': note.message,
            'is_read': is_read
        })
    return JsonResponse({'notifications': notifications, 'unread_count': unread_count})
@login_required
def staff_attendance_view(request):
    context = set_config(request)
    staff = Staff.objects.get(user=request.user)
    assigned_subjects = SemesterSubject.objects.filter(
        models.Q(staff1=staff) | models.Q(staff2=staff) | models.Q(staff3=staff)
    )
    success = None
    error = None
    if request.method == "POST":
        # Find which subject and section this POST is for by parsing POST keys
        subject_id = None
        section_val = None
        date_str = None
        absent_last3 = None
        for key in request.POST.keys():
            if key.startswith("attendance_date_"):
                # Format: attendance_date_{subject_id}_{section}
                parts = key.split("_")
                if len(parts) >= 4:
                    subject_id = parts[2]
                    section_val = parts[3]
                    date_str = request.POST.get(key)
                    absent_key = f"absent_last3_{subject_id}_{section_val}"
                    absent_last3 = request.POST.get(absent_key, '')
                    break
        if subject_id and section_val and date_str:
            try:
                subject = SemesterSubject.objects.get(id=subject_id)
                section = int(section_val)
                date_obj = timezone.datetime.strptime(date_str, "%Y-%m-%d").date()
                students = Student.objects.filter(
                    department=subject.semester.department,
                    semester=subject.semester.semester,
                    section=section
                ).order_by('name')
                absent_last3_list = [s.strip() for s in absent_last3.replace(",", " ").split() if s.strip()]
                for student in students:
                    last3 = str(student.roll)[-3:] if student.roll else None
                    status = 'Absent' if last3 in absent_last3_list else 'Present'
                    att, created = Attendance.objects.get_or_create(
                        subject=subject,
                        student=student,
                        date=date_obj,
                        defaults={'status': status}
                    )
                    if not created:
                        att.status = status
                        att.save()
                success = f"Attendance marked for {subject.name} section {section} on {date_str}."
            except Exception as e:
                error = f"Error: {e}"
    # Prepare context for template
    subjects_with_students = []
    for subject in assigned_subjects:
        semester_obj = subject.semester
        section_students = []
        for idx, (section_field, staff_field) in enumerate([
            ("section1", "staff1"), ("section2", "staff2"), ("section3", "staff3")
        ], start=1):
            section_val = getattr(subject, section_field)
            staff_val = getattr(subject, staff_field)
            if staff_val == staff and section_val is not None:
                students = Student.objects.filter(
                    department=semester_obj.department,
                    semester=semester_obj.semester,
                    section=section_val
                ).order_by('name')
                students_with_attendance = []
                for student in students:
                    total = Attendance.objects.filter(student=student, subject=subject).count()
                    present = Attendance.objects.filter(student=student, subject=subject, status='Present').count()
                    percentage = (present / total * 100) if total > 0 else 0
                    students_with_attendance.append({
                        'student': student,
                        'percentage': round(percentage, 2),
                        'total': total,
                        'present': present
                    })
                section_students.append((section_val, students_with_attendance))
        subjects_with_students.append({
            'subject': subject,
            'section_students': section_students
        })
    context['subjects_with_students'] = subjects_with_students
    context['success'] = success
    context['error'] = error
    return render(request, 'staff/attendance.html', context)

# Student attendance view: show each subject's percentage
@login_required
def student_attendance_view(request):
    context = set_config(request)
    student = Student.objects.get(user=request.user)
    # Get all subjects for this student: department+semester (non-electives) + assigned electives only
    subjects_qs = SemesterSubject.objects.filter(
        semester__department=student.department,
        semester__semester=student.semester,
        is_elective=False
    )
    electives = [student.elective1, student.elective2, student.elective3]
    electives = [e for e in electives if e]
    subjects = list(subjects_qs) + electives
    # Remove duplicates
    subjects = list({s.id: s for s in subjects}.values())
    subject_percentages = []
    for subject in subjects:
        subj_total = Attendance.objects.filter(student=student, subject=subject).count()
        subj_present = Attendance.objects.filter(student=student, subject=subject, status='Present').count()
        subj_percentage = (subj_present / subj_total * 100) if subj_total > 0 else 0
        subject_percentages.append({
            'subject': subject,
            'percentage': round(subj_percentage, 2)
        })
    context['subject_percentages'] = subject_percentages
    context['subjects'] = subjects
    # Recent per-subject absences so students can see dates and subject names
    recent_absences = Attendance.objects.filter(student=student, status='Absent').select_related('subject').order_by('-date')[:200]
    # Group absences by subject (subject may be None)
    grouped = {}
    for a in recent_absences:
        key = a.subject.id if a.subject else 'general'
        if key not in grouped:
            grouped[key] = {
                'subject': a.subject,
                'subject_name': a.subject.name if a.subject else 'General',
                'absences': []
            }
        grouped[key]['absences'].append(a)
    # Convert to a list preserving order (most recent subject groups first by first absence date)
    grouped_absences = []
    for grp in grouped.values():
        grp['count'] = len(grp['absences'])
        grouped_absences.append(grp)
    context['recent_absences'] = recent_absences
    context['grouped_absences'] = grouped_absences
    return render(request, 'student/attendance.html', context)

from django.shortcuts import render
from .models import Department

from django.shortcuts import get_object_or_404

@login_required
@user_passes_test(lambda u: hasattr(u, 'principal_status') and u.principal_status, login_url='/login/')
def principal_department(request):
    from django.urls import reverse
    from .models import Staff, Student
    departments = Department.objects.all()
    for dept in departments:
        # Staff logic
        staff_list = Staff.objects.filter(department=dept)
        for staff in staff_list:
            staff.mentees_url = reverse('view_mentees', args=[staff.id])
        dept.staff_list = staff_list
        dept.staff_count = staff_list.count()
        # Student logic
        student_list = Student.objects.filter(department=dept)
        dept.student_list = student_list
        dept.student_count = student_list.count()
    return render(request, 'principal/department.html', {'departments': departments})

# New view for students by department
@login_required
@user_passes_test(lambda u: hasattr(u, 'principal_status') and u.principal_status, login_url='/login/')
def principal_department_students(request, dept_id):
    from .models import Student, Department
    department = get_object_or_404(Department, id=dept_id)
    # Group students by section and order by section, then name
    students = Student.objects.filter(department=department).order_by('section', 'name')
    # Build a dict: section -> list of students
    from collections import defaultdict
    section_map = defaultdict(list)
    for student in students:
        section_map[student.section].append(student)
    # Get section labels from SECTION choices
    from core.constants import SECTION
    section_labels = {code: label for code, label in SECTION}
    # Prepare ordered sections
    ordered_sections = sorted(section_map.keys())
    section_data = [
        {
            'section_code': sec,
            'section_label': section_labels.get(sec, str(sec)),
            'students': section_map[sec]
        }
        for sec in ordered_sections
    ]
    return render(request, 'principal/department_students.html', {
        'department': department,
        'section_data': section_data
    })

# New view for staff by department
@login_required
@user_passes_test(lambda u: hasattr(u, 'principal_status') and u.principal_status, login_url='/login/')
def principal_department_staff(request, dept_id):
    from .models import Staff, Department
    department = get_object_or_404(Department, id=dept_id)
    staff_list = Staff.objects.filter(department=department).order_by('name')
    return render(request, 'principal/department_staff.html', {'department': department, 'staff_list': staff_list})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
# Student OD history view
@login_required
def student_od_history(request):
    context = set_config(request)
    student = context.get('duser')  # This is the Student object for the logged-in user
    ods = OD.objects.filter(user=student)
    context['ods'] = ods
    return render(request, 'student/od_history.html', context)

# Student Leave history view
@login_required
def student_leave_history(request):
    context = set_config(request)
    student = context.get('duser')  # This is the Student object for the logged-in user
    leaves = LEAVE.objects.filter(user=student)
    context['leaves'] = leaves
    return render(request, 'student/leave_history.html', context)

# Student Bonafide history view
@login_required
def student_bonafide_history(request):
    context = set_config(request)
    student = context.get('duser')  # This is the Student object for the logged-in user
    bonafides = BONAFIDE.objects.filter(user=student)
    context['bonafides'] = bonafides
    return render(request, 'student/bonafide_history.html', context)

# Student Gatepass history view
@login_required
def student_gatepass_history(request):
    context = set_config(request)
    student = context.get('duser')  # This is the Student object for the logged-in user
    gatepasses = GATEPASS.objects.filter(user=student)
    context['gatepasses'] = gatepasses
    return render(request, 'student/gatepass_history.html', context)

@login_required
def staff_list(request):
    context = set_config(request)
    user = request.user
    # Get HOD staff object
    try:
        hod_staff = Staff.objects.get(user=user)
        department = hod_staff.department
        staff_members = Staff.objects.filter(department=department).exclude(id=hod_staff.id)
    except Staff.DoesNotExist:
        staff_members = Staff.objects.none()
    # Ensure each staff has an email, fallback to user.email if not set
    for staff in staff_members:
        if not staff.email and staff.user and hasattr(staff.user, 'email') and staff.user.email:
            staff.email = staff.user.email
        # Fallback for mobile
        if (not staff.mobile or staff.mobile == '') and staff.user and hasattr(staff.user, 'mobile') and staff.user.mobile:
            staff.mobile = staff.user.mobile
    context['staff_members'] = staff_members
    return render(request, 'staff_list.html', context)


from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import get_user_model
from django.utils import timezone
import random
from django.core.mail import send_mail
from django.conf import settings

# View for HOD to see all staff in their department
from django.contrib.auth.decorators import login_required

# --- QR Scan Processing View ---
from django.http import JsonResponse
from core.models import GATEPASS, Student

@login_required
def process_gatepass_qr_scan(request):
    """
    Expects POST with: gatepass_id, scan_type ('exit' or 'entry')
    Updates the corresponding timestamp in GATEPASS.
    """
    if request.method == 'POST':
        gatepass_id = request.POST.get('gatepass_id')
        scan_type = request.POST.get('scan_type')
        try:
            gatepass = GATEPASS.objects.get(id=gatepass_id, user__user=request.user)
        except GATEPASS.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Gatepass not found.'}, status=404)
        now = timezone.now()
        if scan_type == 'exit':
            gatepass.exit_time = now
            gatepass.save()
            return JsonResponse({'success': True, 'message': 'Exit time recorded.', 'exit_time': str(now)})
        elif scan_type == 'entry':
            gatepass.entry_time = now
            gatepass.save()
            return JsonResponse({'success': True, 'message': 'Entry time recorded.', 'entry_time': str(now)})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid scan type.'}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .models import BONAFIDE, GATEPASS, Staff, AHOD, HOD, Notification, Student
from .models import SemesterSubject
from django.db import models
# Principal dashboard view

@login_required
@user_passes_test(lambda u: hasattr(u, 'principal_status') and u.principal_status, login_url='/login/')
def principal_dashboard(request):
    return render(request, 'principal/dashboard.html', {})

from django.http import HttpResponse

@login_required
def ahod_bonafide_hod(request):
    context = set_config(request)
    ahod = AHOD.objects.filter(user=context['duser']).first()
    # Get HODs in the same department as AHOD
    hods = HOD.objects.filter(department=ahod.department) if ahod else HOD.objects.none()
    hod_staff_ids = [h.user.id for h in hods]
    # Get bonafide requests assigned to HODs in this department, pending HOD action
    bonafide_forms = BONAFIDE.objects.filter(user__hod_id__in=hod_staff_ids).distinct()
    # Only show requests where the mentor is the current AHOD (not HODs as mentor)
    mentee_bonafide_forms = BONAFIDE.objects.filter(user__mentor_id=context['duser'].id).distinct()
    context['bonafide_forms'] = bonafide_forms
    context['mentee_bonafide_forms'] = mentee_bonafide_forms
    if request.method == 'POST':
        bonafide_id = request.POST.get('bonafide_id')
        action = request.POST.get('action') or request.POST.get('sts')
        reason = request.POST.get('reason')
        role = request.POST.get('role')
        bonafide = BONAFIDE.objects.get(id=bonafide_id)
        if role == 'mentor':
            if action == 'Approved':
                bonafide.Mstatus = 'Approved by AHOD'
            elif action == 'Rejected':
                bonafide.Mstatus = 'Rejected by AHOD'
            bonafide.ahod_reason = reason
            bonafide.save()
            Notification.objects.create(
                student=bonafide.user,
                message=f"Your Bonafide request was {bonafide.Mstatus} (Reason: {reason})"
            )
        else:
            if action == 'approve':
                bonafide.Hstatus = 'Approved by AHOD'
            elif action == 'reject':
                # If AHOD rejects for HOD role, reject all statuses and notify all
                bonafide.Hstatus = 'Rejected by AHOD'
                bonafide.Mstatus = 'Rejected by AHOD'
                bonafide.Astatus = 'Rejected by AHOD'
                bonafide.ahod_reason = reason
                bonafide.save()
                # Notify student
                Notification.objects.create(
                    student=bonafide.user,
                    message=f"Your Bonafide request was {bonafide.Hstatus} (Reason: {reason})"
                )
                # Notify mentor if exists
                if bonafide.user.mentor:
                    Notification.objects.create(
                        staff=bonafide.user.mentor,
                        role='mentor',
                        message=f"Bonafide request for {bonafide.user.name} was rejected by AHOD."
                    )
                # Notify advisor if exists
                if bonafide.user.advisor:
                    Notification.objects.create(
                        staff=bonafide.user.advisor,
                        role='advisor',
                        message=f"Bonafide request for {bonafide.user.name} was rejected by AHOD."
                    )
                return redirect('ahod_bonafide_hod')
            bonafide.ahod_reason = reason
            bonafide.save()
            Notification.objects.create(
                student=bonafide.user,
                message=f"Your Bonafide request was {bonafide.Hstatus} (Reason: {reason})"
            )
        return redirect('ahod_bonafide_hod')
    return render(request, 'ahod/bonafide_hod.html', context)

# AHOD Gatepass (HOD) requests view
@login_required
def ahod_gatepass_hod(request):
    context = set_config(request)
    ahod = AHOD.objects.filter(user=context['duser']).first()
    hods = HOD.objects.filter(department=ahod.department) if ahod else HOD.objects.none()
    hod_staff_ids = [h.user.id for h in hods]
    gatepass_forms = GATEPASS.objects.filter(user__hod_id__in=hod_staff_ids).distinct()
    # Only show requests where the mentor is the current AHOD (not HODs as mentor)
    mentee_gatepass_forms = GATEPASS.objects.filter(user__mentor_id=context['duser'].id).distinct()
    context['gatepass_forms'] = gatepass_forms
    context['mentee_gatepass_forms'] = mentee_gatepass_forms
    if request.method == 'POST':
        gatepass_id = request.POST.get('gatepass_id')
        action = request.POST.get('action') or request.POST.get('sts')
        reason = request.POST.get('reason')
        role = request.POST.get('role')
        gatepass = GATEPASS.objects.get(id=gatepass_id)
        if role == 'mentor':
            if action == 'Approved':
                gatepass.Mstatus = 'Approved by AHOD'
            elif action == 'Rejected':
                gatepass.Mstatus = 'Rejected by AHOD'
            gatepass.ahod_reason = reason
            gatepass.save()
            Notification.objects.create(
                student=gatepass.user,
                message=f"Your Gatepass request was {gatepass.Mstatus} (Reason: {reason})"
            )
        else:
            if action == 'approve':
                # Set all statuses to 'Approved' so HOD table reflects the change
                gatepass.Hstatus = 'Approved'
                gatepass.Mstatus = 'Approved'
                gatepass.Astatus = 'Approved'
            elif action == 'reject':
                # If AHOD rejects for HOD role, reject all statuses and notify all
                gatepass.Hstatus = 'Rejected'
                gatepass.Mstatus = 'Rejected'
                gatepass.Astatus = 'Rejected'
                gatepass.ahod_reason = reason
                gatepass.save()
                # Notify student
                Notification.objects.create(
                    student=gatepass.user,
                    message=f"Your Gatepass request was {gatepass.Hstatus} (Reason: {reason})"
                )
                # Notify mentor if exists
                if gatepass.user.mentor:
                    Notification.objects.create(
                        staff=gatepass.user.mentor,
                        role='mentor',
                        message=f"Gatepass request for {gatepass.user.name} was rejected by AHOD."
                    )
                # Notify advisor if exists
                if gatepass.user.advisor:
                    Notification.objects.create(
                        staff=gatepass.user.advisor,
                        role='advisor',
                        message=f"Gatepass request for {gatepass.user.name} was rejected by AHOD."
                    )
                return redirect('ahod_gatepass_hod')
            gatepass.ahod_reason = reason
            gatepass.save()
            Notification.objects.create(
                student=gatepass.user,
                message=f"Your Gatepass request was {gatepass.Hstatus} (Reason: {reason})"
            )
        return redirect('ahod_gatepass_hod')
    return render(request, 'ahod/gatepass_hod.html', context)

@login_required
def ahod_notification_history(request):
    ahod = None
    if hasattr(request, 'duser'):
        ahod = getattr(request, 'duser', None)
    if not ahod:
        try:
            ahod = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            ahod = None
    # Only allow AHODs
    if not ahod or not hasattr(ahod, 'position2') or ahod.position2 != 1:
        return render(request, 'ahod/notification_history.html', {'all_notifications': [], 'duser': ahod})
    # Query notifications for AHOD
    all_notifications = Notification.objects.filter(staff=ahod, role__iexact='ahod').order_by('-created_at')
    if request.method == "POST" and 'delete_all' in request.POST:
        all_notifications.delete()
        return redirect('hod_notification_history')
    elif request.method == "POST":
        all_notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'ahod/notification_history.html', {
        'all_notifications': all_notifications,
        'duser': ahod
    })

# View to handle delete all notifications POST
@login_required
def delete_all_notifications(request):
    ahod = None
    if hasattr(request, 'duser'):
        ahod = getattr(request, 'duser', None)
    if not ahod:
        try:
            ahod = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            ahod = None
    if not ahod or not hasattr(ahod, 'position2') or ahod.position2 != 1:
        return redirect('hod_notification_history')
    Notification.objects.filter(staff=ahod, role__iexact='ahod').delete()
    return redirect('hod_notification_history')


@login_required
def my_class_students(request):
    # removed Attendance import
    from django.utils import timezone
    staff = Staff.objects.get(user=request.user)
    students = Student.objects.filter(advisor=staff).order_by('roll')
    context = {
        'students': students,
        'duser': staff,
    }
    # Do not calculate or display attendance percentages
    context['student_percentages'] = {}
    context['selected_date'] = ''
    return render(request, 'staff/my_class_students.html', context)

@login_required
def ahod_dash(request):
    context = set_config(request)
    ahod = AHOD.objects.filter(user=context['duser']).first()
    if not ahod:
        # Show a user-friendly error page or message
        return render(request, 'ahod/ahod_dashboard.html', {
            'error': 'AHOD record not found for your account. Please contact admin.',
            'duser': context.get('duser'),
        })
    # Fetch last 5 notifications for the AHOD
    from .models import Notification
    context['recent_notifications'] = Notification.objects.filter(staff=ahod.user, role__iexact='ahod').order_by('-created_at')[:5]
    return render(request, 'ahod/dash.html', context)



@login_required
def hod_notification_history(request):
    staff = None
    if hasattr(request, 'duser'):
        staff = getattr(request, 'duser', None)
    if not staff:
        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            staff = None
    if not staff or not hasattr(staff, 'position') or staff.position != 0:
        return render(request, 'hod/hod_notification_history.html', {'notifications': [], 'duser': staff})
    notifications = Notification.objects.filter(staff=staff, role__iexact='hod').order_by('-created_at')
    if request.method == "POST" and 'delete_all' in request.POST:
        notifications.delete()
        return redirect('hod_notification_history')
    elif request.method == "POST":
        notifications.filter(is_read=False).update(is_read=True)
    recent_notifications = notifications[:5]
    return render(request, 'hod/hod_notification_history.html', {
        'notifications': notifications,
        'recent_notifications': recent_notifications,
        'duser': staff
    })

# View to handle delete all notifications POST for HOD
@login_required
def delete_all_hod_notifications(request):
    staff = None
    if hasattr(request, 'duser'):
        staff = getattr(request, 'duser', None)
    if not staff:
        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            staff = None
    if not staff or not hasattr(staff, 'position') or staff.position != 0:
        return redirect('hod_notification_history')
    Notification.objects.filter(staff=staff, role__iexact='hod').delete()
    return redirect('hod_notification_history')
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification, Student
from .models import Staff

# Student notifications view
@login_required
def notifications_view(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return render(request, "student/notification_history.html", {"error": "No student record found for this user."})
    latest_unread = Notification.objects.filter(student=student, is_read=False)[:5]
    all_notifications = Notification.objects.filter(student=student)
    if request.method == "POST" and 'delete_all' in request.POST:
        Notification.objects.filter(student=student).delete()
        return redirect('notifications_view')
    elif request.method == "POST":
        Notification.objects.filter(student=student, is_read=False).update(is_read=True)
    context = {
        "latest_unread": latest_unread,
        "all_notifications": all_notifications,
        "duser": student,
    }
    return render(request, "student/notification_history.html", context)

# Circular detail view (accessible from notifications)
@login_required
def circular_detail(request, pk):
    from .models import Circular
    try:
        c = Circular.objects.get(id=pk, published=True)
    except Circular.DoesNotExist:
        return render(request, '404.html', status=404)
    # Ensure we include the standard context (duser, GP, etc.)
    context = set_config(request)
    context['circular'] = c
    return render(request, 'student/circular_detail.html', context)

# View to handle delete all notifications POST for students
@login_required
def delete_all_student_notifications(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return redirect('notifications_view')
    Notification.objects.filter(student=student).delete()
    return redirect('notifications_view')

# Staff notifications view
@login_required
def staff_notifications_view(request):
    staff = None
    # Try to get staff from context if available
    if 'duser' in request.session or 'duser' in request.__dict__ or hasattr(request, 'duser'):
        staff = getattr(request, 'duser', None)
    if not staff:
        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            staff = None
    if not staff:
        return redirect('login')
    # Only show HOD notifications for HOD users
    if hasattr(staff, 'position') and staff.position == 0:  # HOD position
        latest_unread = Notification.objects.filter(staff=staff, role='hod', is_read=False).order_by('-created_at')[:5]
        all_notifications = Notification.objects.filter(staff=staff, role='hod').order_by('-created_at')
        unread_count = Notification.objects.filter(staff=staff, role='hod', is_read=False).count()
    else:
        latest_unread = Notification.objects.filter(staff=staff, is_read=False).order_by('-created_at')[:5]
        all_notifications = Notification.objects.filter(staff=staff).order_by('-created_at')
        unread_count = Notification.objects.filter(staff=staff, is_read=False).count()
        if request.method == "POST" and 'delete_all' in request.POST:
            Notification.objects.filter(staff=staff).delete()
            return redirect('staff_notifications')
        elif request.method == "POST":
            Notification.objects.filter(staff=staff, is_read=False).update(is_read=True)
    return render(request, "staff/notification_history.html", {
        "latest_unread": latest_unread,
        "all_notifications": all_notifications,
        "unread_count": unread_count,
        "duser": staff,
    })


# View to handle delete all notifications POST for staff
@login_required
def delete_all_staff_notifications(request):
    staff = None
    if hasattr(request, 'duser'):
        staff = getattr(request, 'duser', None)
    if not staff:
        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            staff = None
    if not staff:
        return redirect('login')
    Notification.objects.filter(staff=staff).delete()
    return redirect('staff_notifications')

@login_required
def ahod_od_view(request):
    context = set_config(request)
    from .models import Staff, AHOD, OD
    from django.db.models import Q
    try:
        duser = Staff.objects.get(user=request.user)
    except Staff.DoesNotExist:
        duser = None
    context['duser'] = duser
    ahod = AHOD.objects.filter(user=duser).first() if duser else None
    # Mentees: ODs where duser is mentor or advisor
    context['mods'] = OD.objects.filter(Q(user__mentor=duser) | Q(user__advisor=duser)).distinct()
    # Dept ODs: all ODs for students in AHOD's department
    if ahod and hasattr(ahod, 'user') and hasattr(ahod.user, 'department'):
        context['hods'] = OD.objects.filter(user__department=ahod.user.department).distinct()
    else:
        context['hods'] = OD.objects.none()
    return render(request, 'ahod/ods.html', context)

@login_required
def ahod_leave_view(request):
    from django.db.models import Q
    context = set_config(request)
    ahod = AHOD.objects.get(user=context['duser'])
    # Mentees: students where AHOD is mentor
    context['mods'] = LEAVE.objects.filter(user__mentor=ahod.user)
    # Dept leaves: all leaves for students in AHOD's department (match ODs logic)
    dept = getattr(ahod.user, 'department', None)
    if dept:
        context['hods'] = LEAVE.objects.filter(user__department=dept).order_by('-created')
    else:
        context['hods'] = LEAVE.objects.none()
    return render(request, 'ahod/leaves.html', context)

# Student Profile View
@login_required
def student_profile(request):
    from .models import AHOD, HOD
    context = set_config(request)
    student = context.get('duser')
    # Allow the logged-in student to edit their own profile (name, dob, mobile, address)
    can_edit = False
    try:
        if student and hasattr(student, 'user') and student.user == request.user:
            can_edit = True
    except Exception:
        can_edit = False
    context['can_edit'] = can_edit

    # Handle POST (save edits)
    if request.method == 'POST' and can_edit:
        # Extract fields from POST
        new_name = request.POST.get('name')
        new_dob = request.POST.get('dob')
        new_mobile = request.POST.get('mobile')
        new_address = request.POST.get('address')
        changed = False
        # Update fields where provided
        if new_name is not None and new_name.strip() != '' and new_name.strip() != (student.name or '').strip():
            student.name = new_name.strip()
            changed = True
        if new_dob:
            # Expecting YYYY-MM-DD; let Django parse when assigning (Field will cast)
            try:
                from datetime import datetime
                dob_parsed = datetime.strptime(new_dob, '%Y-%m-%d').date()
                if student.dob != dob_parsed:
                    student.dob = dob_parsed
                    changed = True
            except Exception:
                # ignore parse errors — could add messages but keep silent for now
                pass
        if new_mobile is not None and new_mobile.strip() != '':
            # store numeric mobile if possible
            try:
                mobile_val = int(new_mobile)
                if student.mobile != mobile_val:
                    student.mobile = mobile_val
                    changed = True
            except Exception:
                # if not integer, store raw string fallback to avoid data loss
                try:
                    student.mobile = int(''.join(filter(str.isdigit, new_mobile)))
                    changed = True
                except Exception:
                    pass
        if new_address is not None and new_address.strip() != '' and new_address.strip() != (student.address or '').strip():
            student.address = new_address.strip()
            changed = True

        if changed:
            student.save()
            from django.contrib import messages
            messages.success(request, 'Profile updated successfully.')
        return redirect('student_profile')
    dept_ahod = None
    dept_hod = None
    # Prefer direct relation if set
    if hasattr(student, 'ahod') and student.ahod:
        dept_ahod = student.ahod
    if hasattr(student, 'hod') and student.hod:
        dept_hod = HOD.objects.filter(user=student.hod).first()
    # Fallback to department match if not set
    if not dept_ahod or not dept_hod:
        if hasattr(student, 'department') and student.department is not None:
            try:
                dept_code = int(student.department)
                if not dept_ahod:
                    dept_ahod = AHOD.objects.filter(department=dept_code).first()
                if not dept_hod:
                    dept_hod = HOD.objects.filter(department=dept_code).first()
            except Exception:
                pass
    context['dept_ahod'] = dept_ahod
    context['dept_hod'] = dept_hod
    # If user requested edit mode via ?edit=1 and they can edit, enable editing UI
    editing = request.GET.get('edit') == '1' and can_edit
    context['editing'] = editing
    return render(request, 'common/profile.html', context)


@login_required
def hod_bonafide_view(request):
    context = set_config(request)
    context['bonafide_forms'] = BONAFIDE.objects.none()
    if 'duser' in context:
        try:
            hod_staff = Staff.objects.get(user=context['duser'].user)
            forms = BONAFIDE.objects.filter(
                models.Q(user__mentor=hod_staff) |
                models.Q(user__advisor=hod_staff) |
                models.Q(user__hod=hod_staff)
            ).distinct()
            if forms.exists():
                context['bonafide_forms'] = forms
        except Staff.DoesNotExist:
            pass
    return render(request, "hod/bonafide_hod.html", context)
def dash(request):
    context = set_config(request)
    if 'duser' not in context:
        return redirect('login')

    # --- Add today's timetable for staff dashboard ---
    if request.user.is_staff:
        # Check if the user is a PET Staff and redirect (check all position fields)
        if hasattr(request.user, 'staff'):
            staff_obj = request.user.staff
            if (
                getattr(staff_obj, 'position', None) == 5 or
                getattr(staff_obj, 'position2', None) == 5 or
                getattr(staff_obj, 'position3', None) == 5
            ):
                return redirect('pet_dashboard')
            else:
                # Debug: Not PET Staff, show message
                from django.contrib import messages
                messages.warning(request, f"Staff detected but position(s)={staff_obj.position},{staff_obj.position2},{staff_obj.position3}, not PET Staff (5).")
        else:
            # Debug: No Staff object linked
            from django.contrib import messages
            messages.warning(request, "No Staff object linked to this user. PET Staff portal not available.")
        from core.services.get_todays_timetable import get_todays_timetable
        context['todays_timetable'] = get_todays_timetable(context['duser'])

    if not request.user.is_staff:
        from django.utils import timezone
        today = timezone.now().date()
        # Today's applications
        context['ods_today'] = OD.objects.filter(user=context['duser'], created__date=today)
        context['leaves_today'] = LEAVE.objects.filter(user=context['duser'], created__date=today)
        context['bonafides_today'] = BONAFIDE.objects.filter(user=context['duser'], created__date=today)
        context['gatepasses_today'] = GATEPASS.objects.filter(user=context['duser'], created__date=today)
        # All applications for 'View All'
        context['ods_all'] = OD.objects.filter(user=context['duser'])
        context['leaves_all'] = LEAVE.objects.filter(user=context['duser'])
        context['bonafides_all'] = BONAFIDE.objects.filter(user=context['duser'])
        context['gatepasses_all'] = GATEPASS.objects.filter(user=context['duser'])
        # Fetch last 5 notifications for the logged-in student
        student = context['duser'] if isinstance(context['duser'], Student) else Student.objects.filter(user=request.user).first()
        context['recent_notifications'] = Notification.objects.filter(student=student).order_by('-created_at')[:5]
        return render(request, 'student/dash.html', context=context)

    elif context['duser'].position == 0 or AHOD.objects.filter(user=context['duser']).exists() or context['duser'].position2 == 1:
        # HOD or AHOD or Assistant Head of Department
        # If HOD, use HOD logic (removed staff ratings and recent logs display)
        if context['duser'].position == 0:
            hod = HOD.objects.get(user=context['duser'])
            try:
                hod_staff = Staff.objects.get(user=context['duser'].user)
                context['bonafides'] = BONAFIDE.objects.filter(
                    models.Q(user__mentor=hod_staff) |
                    models.Q(user__advisor=hod_staff) |
                    models.Q(user__hod=hod_staff)
                ).distinct()
            except Staff.DoesNotExist:
                context['bonafides'] = BONAFIDE.objects.none()
            # Fetch last 5 notifications for the HOD
            context['recent_notifications'] = Notification.objects.filter(staff=hod_staff, role__iexact='hod').order_by('-created_at')[:5]
            return render(request, "hod/dash.html", context)
        # If AHOD or Assistant HOD, show all student applications for their department
        else:
            # Find the AHOD object for this user
            ahod = AHOD.objects.filter(user=context['duser']).first()
            if ahod:
                staff_list = list(ahod.staffs.all())
                staff_list.append(ahod.user)
            else:
                staff_list = [context['duser']]
            context['all_od'] = OD.objects.filter(
                models.Q(user__advisor__in=staff_list) |
                models.Q(user__mentor__in=staff_list) |
                models.Q(user__hod__in=staff_list)
            ).distinct()
            context['all_leave'] = LEAVE.objects.filter(
                models.Q(user__advisor__in=staff_list) |
                models.Q(user__mentor__in=staff_list) |
                models.Q(user__hod__in=staff_list)
            ).distinct()
            return render(request, "ahod/dash.html", context)

    else:
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        one_day_ago = now - timedelta(days=1)
        staff = context['duser']
        # Fetch all mentee requests for all forms where user is mentor, advisor, or HOD
        context['recent_od'] = OD.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff),
            created__gte=one_day_ago
        ).order_by('-created')[:5]
        context['recent_leave'] = LEAVE.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff),
            created__gte=one_day_ago
        ).order_by('-created')[:5]
        context['recent_gatepass'] = GATEPASS.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff),
            created__gte=one_day_ago
        ).order_by('-created')[:5]
        context['recent_bonafide'] = BONAFIDE.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff),
            created__gte=one_day_ago
        ).order_by('-created')[:5]
        # All mentee requests for all forms
        context['mentee_ods'] = OD.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff)
        ).distinct()
        context['mentee_leaves'] = LEAVE.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff)
        ).distinct()
        context['mentee_gatepasses'] = GATEPASS.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff)
        ).distinct()
        context['mentee_bonafides'] = BONAFIDE.objects.filter(
            models.Q(user__advisor=staff) | models.Q(user__mentor=staff) | models.Q(user__hod=staff)
        ).distinct()
        # Fetch last 5 notifications for the staff
        context['recent_notifications'] = Notification.objects.filter(staff=staff).order_by('-created_at')[:5]
        return render(request, 'staff/dash.html', context)



def login_user(request):

    context = {}
    if request.POST:
        reg = request.POST.get('reg')
        pwd = request.POST.get('pass')
        error_msg = None
        try:
            user_obj = User.objects.get(username=reg)
            user = authenticate(request, username=reg, password=pwd)
            if user is not None:
                login(request, user)
                # Redirect PET staff directly to PET dashboard (check all positions)
                if (
                    user.is_staff and hasattr(user, 'staff') and (
                        getattr(user.staff, 'position', None) == 5 or
                        getattr(user.staff, 'position2', None) == 5 or
                        getattr(user.staff, 'position3', None) == 5
                    )
                ):
                    return redirect('pet_dashboard')
                return redirect(settings.LOGIN_REDIRECT_URL)
            else:
                error_msg = "Wrong Password"
        except User.DoesNotExist:
            error_msg = "Wrong Register Number"
        context['error_msg'] = error_msg

    return render(request, 'auth/login.html', context)

from django.views.decorators.cache import never_cache

@login_required
@never_cache
def logout_user(request):
    logout(request)
    response = redirect('dash')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

# HOD MODULE
@login_required


def od(request):
    context = set_config(request)

    if request.method == "POST":
        sub = get_post(request, 'sub')
        body = get_post(request, 'reason')
        start = get_post(request, 'start')
        end = get_post(request, 'end')
        proof = request.FILES.get('proof')

        # Convert browser datetime string → Python datetime
        start = parse_datetime(start)
        end = parse_datetime(end)
        from django.utils import timezone
        if start and timezone.is_naive(start):
            start = timezone.make_aware(start)
        if end and timezone.is_naive(end):
            end = timezone.make_aware(end)

        # Create OD request
        obj = OD.objects.create(
            user=context['duser'],
            sub=sub,
            body=body,
            start=start,
            end=end,
            proof=proof
        )

        # Notify mentor, advisor, HOD, AHOD
        student = context['duser']
        staff_list = [
            (student.mentor, 'mentor'),
            (student.advisor, 'advisor'),
            (student.hod, 'hod'),
            (student.ahod.user if student.ahod else None, 'ahod'),
        ]
        for staff, role in staff_list:
            if staff:
                Notification.objects.create(
                    staff=staff,
                    role=role,
                    message=f"New OD request from {student.name}"
                )

        return redirect("dash")

    return render(request, 'student/od.html', context=context)



@login_required
def leave(request):
    context = set_config(request)
    if request.POST:
        from django.utils import timezone
        from datetime import datetime
        sub = get_post(request, 'sub')
        body = get_post(request, 'reason')
        f_raw = get_post(request, "from")
        t_raw = get_post(request, 'to')
        proff = request.FILES.get('proof')
        # Parse datetime fields, fallback to now if missing
        try:
            f = datetime.strptime(f_raw, "%Y-%m-%dT%H:%M") if f_raw else timezone.now()
        except Exception:
            f = timezone.now()
        try:
            t = datetime.strptime(t_raw, "%Y-%m-%dT%H:%M") if t_raw else timezone.now()
        except Exception:
            t = timezone.now()
        # Make timezone aware if needed
        if timezone.is_naive(f):
            f = timezone.make_aware(f)
        if timezone.is_naive(t):
            t = timezone.make_aware(t)
        obj = LEAVE(user=context['duser'], sub=sub,
                    body=body, start=f, end=t, proof=proff)
        obj.save()
        # Notify mentor, advisor, HOD, AHOD
        student = context['duser']
        staff_list = [
            (student.mentor, 'mentor'),
            (student.advisor, 'advisor'),
            (student.hod, 'hod'),
            (student.ahod.user if student.ahod else None, 'ahod'),
        ]
        for staff, role in staff_list:
            if staff:
                Notification.objects.create(
                    staff=staff,
                    role=role,
                    message=f"New Leave request from {student.name}"
                )
        return redirect("dash")

    return render(request, 'student/leave.html', context=context)

@login_required
def gatepass(request):
    context = set_config(request)
    action = request.GET.get('action', 'apply')
    context['action'] = action
    if request.method == "POST":
        sub = get_post(request, 'sub')
        start = get_post(request, 'start')
        end = get_post(request, 'end')
        # Parse datetime
        start = parse_datetime(start)
        end = parse_datetime(end)
        obj = GATEPASS(user=context['duser'], sub=sub, start=start, end=end)
        obj.save()

        # Notify mentor, advisor, HOD. Add safe fallbacks if some relations are missing.
        student = context['duser']
        staff_candidates = []
        # Prefer explicit mentor/advisor/hod if present
        for s, r in ((student.mentor, 'mentor'), (student.advisor, 'advisor'), (student.hod, 'hod')):
            if s and s not in staff_candidates:
                staff_candidates.append((s, r))
        # Fallback: if hod missing on student, try department.hod
        try:
            if not student.hod and student.department and student.department.hod:
                # department.hod is a Staff instance
                dept_hod = student.department.hod
                if (dept_hod, 'hod') not in staff_candidates:
                    staff_candidates.append((dept_hod, 'hod'))
        except Exception:
            # ignore fallback errors
            pass

        for staff, role in staff_candidates:
            if staff:
                Notification.objects.create(
                    staff=staff,
                    role=role,
                    message=f"New Gatepass request from {student.name}",
                )
    # Notify mentor, advisor, HOD, AHOD
    if action == 'status':
        # Show all gatepasses for this student
        context['gatepasses'] = GATEPASS.objects.filter(user=context['duser']).order_by('-id')
    return render(request, 'student/gatepass_base.html', context=context)

@login_required
def staff_od_view(request):
    context = set_config(request)

    context['aods'] = [i for i in OD.objects.all() if i.user.advisor.id ==
                       context['duser'].id]
    context['mods'] = [i for i in OD.objects.all() if i.user.mentor.id ==
                       context['duser'].id]

    return render(request, 'staff/ods.html', context)

@login_required
def staff_leave_view(request):
    context = set_config(request)

    context['aods'] = [i for i in LEAVE.objects.all(
    ) if i.user.advisor.id == context['duser'].id]
    context['mods'] = [i for i in LEAVE.objects.all(
    ) if i.user.mentor.id == context['duser'].id]

    return render(request, 'staff/leaves.html', context)

@login_required
def staff_gatepass_view(request):
    context = set_config(request)

    # Guard against students without advisor/mentor set
    context['aods'] = [i for i in GATEPASS.objects.all() if getattr(i.user, 'advisor', None) and i.user.advisor.id == context['duser'].id]
    context['mods'] = [i for i in GATEPASS.objects.all() if getattr(i.user, 'mentor', None) and i.user.mentor.id == context['duser'].id]

    return render(request, 'staff/gatepasss.html', context)

@login_required
def hod_od_view(request):
    context = set_config(request)

    context['mods'] = [i for i in OD.objects.all() if i.user.mentor.id == context['duser'].id]
    context['hods'] = [i for i in OD.objects.all() if i.user.hod.id == context['duser'].id or i.user.mentor.id != context['duser'].id]
    # Ensure OD body is always set for all entries
    for od in context['mods'] + context['hods']:
        if not od.body:
            od.body = "No details provided."
    print(context)
    return render(request, 'hod/ods.html', context)

@login_required
def hod_leave_view(request):
    context = set_config(request)

    context['mods'] = [i for i in LEAVE.objects.all() if i.user.mentor.id == context['duser'].id]
    context['hods'] = [i for i in LEAVE.objects.all() if i.user.hod.id ==
                       context['duser'].id or i.user.mentor.id != context['duser'].id]
    print(context)
    return render(request, 'hod/leaves.html', context)

@login_required
def hod_gatepass_view(request):
    context = set_config(request)

    context['mods'] = [i for i in GATEPASS.objects.all() if getattr(i.user, 'mentor', None) and i.user.mentor.id == context['duser'].id]
    context['hods'] = [i for i in GATEPASS.objects.all() if (getattr(i.user, 'hod', None) and i.user.hod.id == context['duser'].id) or (getattr(i.user, 'mentor', None) and i.user.mentor.id != context['duser'].id)]
    print(context)
    return render(request, 'hod/gatepasss.html', context)

@login_required

@login_required
def staff_action_od(request, id):

    if request.POST:
        od = OD.objects.get(id=id)
        print(f"staff_action_od: mentor={od.user.mentor.user.username}, advisor={od.user.advisor.user.username}, hod={od.user.hod.user.username}, current_user={request.user}")
        role = request.POST.get('role')
        status = get_post(request, 'sts')
        if role == 'mentor' and str(od.user.mentor.user.username) == str(request.user):
            od.Mstatus = status
            if od.Mstatus == STATUS[2][0]:  # Rejected
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
                od.AHstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                student=od.user,
                message=f"Your OD request was {od.Mstatus} by Mentor"
            )
            print(od.Mstatus)
            od.save()
            return redirect("staff_od_view")
        elif role == 'advisor' and str(od.user.advisor.user.username) == str(request.user):
            od.Astatus = status
            print(f"Advisor action: POST['sts']={od.Astatus}, Mentor={od.Mstatus}, Advisor={od.Astatus}, User={request.user}")
            # If advisor is also acting as mentor (mentor is still pending), update mentor status
            if od.Mstatus == STATUS[0][0]:  # Pending
                print("Advisor acting as mentor: updating Mstatus to", od.Astatus)
                od.Mstatus = od.Astatus
            # If advisor rejects, cascade rejection
            if od.Astatus == STATUS[2][0]:  # Rejected
                print("Advisor rejected: cascading rejection to Hstatus and AHstatus")
                od.Hstatus = STATUS[2][0]
                od.AHstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                student=od.user,
                message=f"Your OD request was {od.Astatus} by Advisor"
            )
            print(f"After save: Mentor={od.Mstatus}, Advisor={od.Astatus}, HOD={od.Hstatus}, AHOD={od.AHstatus}")
            od.save()
            return redirect("staff_od_view")
        elif role == 'hod' and str(od.user.hod.user.username) == str(request.user):
            action_status = status
            if action_status == STATUS[1][0]:  # 'Approved'
                od.Mstatus = STATUS[1][0]
                od.Astatus = STATUS[1][0]
                od.Hstatus = STATUS[1][0]
                od.AHstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                od.Mstatus = STATUS[2][0]
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
                od.AHstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                student=od.user,
                message=f"Your OD request was {action_status} by HOD"
            )
            od.save()
            print(od.Astatus)
            return redirect("hod_od_view")
        od.save()
        print("Changed")
    return redirect("staff_od_view")

@login_required
def staff_action_leave(request, id):



    if request.POST:
        leave = LEAVE.objects.get(id=id)
        role = request.POST.get('role')
        status = get_post(request, 'sts')
        print(f"staff_action_leave: mentor={leave.user.mentor.user.username}, advisor={leave.user.advisor.user.username}, hod={leave.user.hod.user.username}, current_user={request.user}, role={role}, status={status}")

        if role == 'mentor' and str(leave.user.mentor.user.username) == str(request.user):
            leave.Mstatus = status
            # Only set other statuses if rejected, not approved
            if leave.Mstatus == STATUS[2][0]:  # Rejected
                leave.Astatus = STATUS[2][0]
                leave.Hstatus = STATUS[2][0]
                leave.AHstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                student=leave.user,
                message=f"Your Leave request was {leave.Mstatus} by Mentor"
            )
            print(leave.Mstatus)
        elif role == 'advisor' and str(leave.user.advisor.user.username) == str(request.user):
            leave.Astatus = status
            # If mentor is still pending, set mentor status to advisor's decision
            if leave.Mstatus == STATUS[0][0]:  # Pending
                leave.Mstatus = leave.Astatus
            if leave.Astatus == STATUS[2][0]:
                leave.Hstatus = STATUS[2][0]
                leave.AHstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                student=leave.user,
                message=f"Your Leave request was {leave.Astatus} by Advisor"
            )
        elif role == 'hod' and str(leave.user.hod.user.username) == str(request.user):
            action_status = status
            if action_status == STATUS[1][0]:  # 'Approved'
                leave.Mstatus = STATUS[1][0]
                leave.Astatus = STATUS[1][0]
                leave.Hstatus = STATUS[1][0]
                leave.AHstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                leave.Mstatus = STATUS[2][0]
                leave.Astatus = STATUS[2][0]
                leave.Hstatus = STATUS[2][0]
                leave.AHstatus = STATUS[2][0]
            from .models import Notification
            Notification.objects.create(
                student=leave.user,
                message=f"Your Leave request was {action_status} by HOD"
            )
            leave.save()
            print(leave.Astatus)
            return redirect("hod_leave_view")

        leave.save()
        print("Changed")

        ref = request.META.get('HTTP_REFERER')
        if ref:
            return redirect(ref)

    return redirect("staff_leave_view")


@login_required
def staff_action_gatepass(request, id):
    if request.POST:
        gatepass = GATEPASS.objects.get(id=id)
        role = request.POST.get('role')
        status = request.POST.get('sts')
        from .models import Notification
        user_is_mentor = str(gatepass.user.mentor.user.username) == str(request.user)
        user_is_advisor = str(gatepass.user.advisor.user.username) == str(request.user)
        # If staff is both mentor and advisor, update both statuses
        if (role == 'mentor' and user_is_mentor) or (role == 'advisor' and user_is_advisor):
            if user_is_mentor and user_is_advisor:
                gatepass.Mstatus = status
                gatepass.Astatus = status
                if status == STATUS[2][0]:
                    gatepass.Hstatus = STATUS[2][0]
                Notification.objects.create(
                    student=gatepass.user,
                    message=f"Your Gatepass request was {status} by Mentor/Advisor"
                )
                gatepass.save()
                return redirect("staff_gatepass_view")
            # If only mentor
            if role == 'mentor' and user_is_mentor:
                gatepass.Mstatus = status
                if status == STATUS[2][0]:  # Rejected
                    gatepass.Astatus = STATUS[2][0]
                    gatepass.Hstatus = STATUS[2][0]
                Notification.objects.create(
                    student=gatepass.user,
                    message=f"Your Gatepass request was {gatepass.Mstatus} by Mentor"
                )
                gatepass.save()
                return redirect("staff_gatepass_view")
            # If only advisor
            if role == 'advisor' and user_is_advisor:
                gatepass.Astatus = status
                if gatepass.Mstatus == STATUS[0][0]:  # Pending
                    gatepass.Mstatus = gatepass.Astatus
                if status == STATUS[2][0]:
                    gatepass.Hstatus = STATUS[2][0]
                Notification.objects.create(
                    student=gatepass.user,
                    message=f"Your Gatepass request was {gatepass.Astatus} by Advisor"
                )
                gatepass.save()
                return redirect("staff_gatepass_view")
        # HOD action
        if role == 'hod' and str(gatepass.user.hod.user.username) == str(request.user):
            if status == STATUS[1][0]:  # Approved
                gatepass.Mstatus = STATUS[1][0]
                gatepass.Astatus = STATUS[1][0]
                gatepass.Hstatus = STATUS[1][0]
            elif status == STATUS[2][0]:  # Rejected
                gatepass.Mstatus = STATUS[2][0]
                gatepass.Astatus = STATUS[2][0]
                gatepass.Hstatus = STATUS[2][0]
            Notification.objects.create(
                student=gatepass.user,
                message=f"Your Gatepass request was {gatepass.Hstatus} by HOD"
            )
            gatepass.save()
            return redirect("hod_gatepass_view")
        gatepass.save()
        # Default: if not mentor/advisor/hod, stay on staff page
        return redirect("staff_gatepass_view")


@login_required
def upload_proof_od(request, id):
    if request.POST:
        comp = request.FILES.get('comp')
        od = OD.objects.get(id=id)
        od.certificate = comp
        od.save()

    return redirect('dash')


@login_required
def upload_proof_leave(request, id):
    if request.POST:
        comp = request.FILES.get('comp')
        od = LEAVE.objects.get(id=id)
        od.certificate = comp
        od.save()

    return redirect('dash')


# Feedback

#hodFeedback View

def hod_feedback_view(request):
    context = set_config(request)
    context['hod'] = HOD.objects.get(user=context['duser'])
    if context['hod'].department == 0:
        context['class'] = SECTION[:2] 
        
    elif context['hod'].department == 1 or context['hod'].department ==3 :
        context['class'] = SECTION[2:]
    
    else :
        context['class'] = SECTION[2]
    
    context['year'] = YEAR 
    
    context['spf'] = SpotFeedback.objects.filter(user=context['duser'])
    
    return render(request,"hod/feedback.html",context)

@login_required
def hod_feedback_toggle(request,id):
    if request.POST:
        obj = HOD.objects.get(id=id)
        obj.get_feedback = not obj.get_feedback
        obj.save()
        
    return redirect('hod_feedback_view')

@login_required
def hod_spot_feedback_toggle(request,id):
    if request.POST:
        obj = SpotFeedback.objects.get(id=id)
        obj.is_open = not obj.is_open
        obj.save()
        
    return redirect('hod_feedback_view')


@login_required
def hod_spot_feedback(request):
    context = set_config(request)
    if request.POST:
        staff = get_post(request,'staff')                           
        year = get_post(request,'yr')                           
        cls = get_post(request,'cls')
        
        students = Student.objects.filter(year=year)
        obj = SpotFeedback(user=context['duser'],staff=Staff.objects.get(id=staff),year=year,section=cls)
        obj.save()
        for i in students:
            obj.students.add(i)
        obj.save()
        context['duser'].get_spot_feedback = True
        context['duser'].save()
        
        hod = HOD.objects.filter(user=context['duser'])[0]
        hod.spot_feedback.add(obj)
        hod.save()
        
        # QR
        
        qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
        obj.url = request.build_absolute_uri(obj.get_absolute_url())
        qr.add_data(obj.url)
        
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        qr_code_image = BytesIO()
        img.save(qr_code_image, format='PNG')
        
         
        obj.qr_code.save(f'fqr_code{obj.id}.png', File(qr_code_image))

        obj.save()
    
    return redirect('hod_feedback_view')


@login_required

def student_feedback(request):
    context = set_config(request)
    duser = context.get('duser')
    from .models import Student
    if not isinstance(duser, Student):
        try:
            duser = Student.objects.get(user=request.user)
            context['duser'] = duser
        except Exception:
            return render(request, 'student/feedback.html', context)

    ques = FeedbackQuestion.objects.all()
    typ = request.GET.get('type', 'gen')
    context['ques'] = ques
    context['typ'] = typ

    context['s_rating'] = []
    context['cs_rating'] = []
    
    hod = HOD.objects.get(user=duser.hod)

    context['ques'] = ques
    context['c_staff'] = Staff.objects.get(id=id)

    if request.POST:
        inrating = IndividualStaffRating(
            staff=context['c_staff'], student=context['duser'])
        inrating.save()
        for i in ques:
            comt = get_post(request, f"comment{i.id}")
            star = get_post(request, f"star{i.id}")
            obj = StaffRating(
                staff=context['c_staff'], student=context['duser'], ques=i, points=star, comments=comt)
            obj.save()
            inrating.ratings.add(obj)
            
        if typ=='gen':
            context['duser'].feedback_for.add(inrating)
            
            
        elif typ=='spf':
            hod = HOD.objects.get(user=context['duser'].hod)
            spot_feedbacks = hod.spot_feedback.filter(staff=context['c_staff'])
            for i in spot_feedbacks:
                if len(i.students.filter(user=context['duser'].user)) > 0:
                    i.feebacks.add(inrating)
                    i.students.remove(context['duser'])
                    i.completed_students.add(context['duser'])
                    i.save()
        else:
            pass
        
        context['duser'].feedback_history.add(inrating)
        context['duser'].save()

        inrating.is_feedbacked = True
        inrating.save()

        context['c_staff'].my_feedbacks.add(inrating)
        context['c_staff'].save()

        # --- Feedback completion notification logic ---
        # Get all students assigned to this staff for the same class/section/year
        staff_obj = context['c_staff']
        # Find students assigned to this staff (same year/section)
        assigned_students = Student.objects.filter(
            year=staff_obj.year,
            section=staff_obj.section,
            teaching_staffs=staff_obj
        )
        # Count how many have submitted feedback for this staff
        completed_count = 0
        for student in assigned_students:
            # Check if student has feedbacked this staff
            if IndividualStaffRating.objects.filter(staff=staff_obj, student=student, is_feedbacked=True).exists():
                completed_count += 1
        if completed_count == assigned_students.count() and assigned_students.count() > 0:
            # Notify HOD only if not already notified for this staff
            hod_staff = staff_obj.hod
            msg = f"Feedback for Dr. {staff_obj.name} is completed by all assigned students."
            if not Notification.objects.filter(staff=hod_staff, role='hod', message__icontains=staff_obj.name).exists():
                Notification.objects.create(
                    staff=hod_staff,
                    role='hod',
                    message=msg
                )
        # --- End feedback completion notification logic ---
        return redirect('student_feedback')

    return render(request, "feedbackform.html", context=context)

# END HOD MODULE

# CSFW


# EDC

# Bonafide View
@login_required
def bonafide_view(request):
    context = set_config(request)
    # Ensure duser is a Student instance
    duser = context.get('duser')
    from .models import Student
    if not isinstance(duser, Student):
        try:
            duser = Student.objects.get(name=duser)
            context['duser'] = duser
        except Exception:
            context['bonafides'] = BONAFIDE.objects.none()
        else:
            context['bonafides'] = BONAFIDE.objects.filter(user=duser)
    else:
        context['bonafides'] = BONAFIDE.objects.filter(user=duser)
    if request.POST:
        sub = get_post(request, 'sub')
        date = get_post(request, 'date')
        proff = request.FILES.get('proof')
        # Compose body from all relevant fields
        body_parts = []
        def add_body(label, key):
            val = get_post(request, key)
            if val:
                body_parts.append(f"{label}: {val}")
        add_body('Father\'s Name', 'fathers_name')
        add_body('Branch', 'branch')
        add_body('Year', 'year')
        add_body('Community', 'community')
        add_body('Other Community', 'other_community')
        add_body('Scholar Type', 'scholar_type')
        add_body('College Bus', 'college_bus')
        add_body('Boarding Point', 'boarding_point')
        add_body('Bus Type', 'bus_type')
        add_body('Bus Fare', 'bus_fare')
        add_body('First Graduate', 'first_graduate')
        add_body('Gov/Management', 'gov_mgmt')
        # Add other_purpose if present and selected
        if get_post(request, 'purpose') == 'Other':
            add_body('Other Purpose', 'other_purpose')
        body = " | ".join(body_parts)
        obj = BONAFIDE(user=context['duser'], sub=sub, body=body, date=date, proof=proff)
        obj.save()

        # Notify mentor, advisor, HOD
        student = context['duser']
        staff_list = [student.mentor, student.advisor, student.hod]
        for staff in staff_list:
            if staff:
                role = 'hod' if hasattr(staff, 'position') and staff.position == 0 else None
                Notification.objects.create(
                    staff=staff,
                    role=role,
                    message=f"New Bonafide request from {student.name}",
                )
    # Notify mentor, advisor, HOD, AHOD
        return redirect("dash")
    return render(request, 'student/bonafide_form.html', context=context)

# Staff Bonafides View
@login_required
def staff_bonafides(request):
    context = set_config(request)
    # Show bonafide requests for students who are mentees of the logged-in staff user
    staff = Staff.objects.get(user=request.user)
    # Bonafide forms for which the logged-in staff is the mentor
    context['mentee_bonafides'] = BONAFIDE.objects.filter(user__mentor=staff)
    # Bonafide forms for which the logged-in staff is the advisor (class forms)
    context['class_bonafides'] = BONAFIDE.objects.filter(user__advisor=staff)
    return render(request, 'staff/bonafides.html', context)

@login_required
def staff_action_bonafide(request, id):
    if request.POST:
        bonafide = BONAFIDE.objects.get(id=id)
        role = request.POST.get('role')
        status = request.POST.get('sts')
        from .models import Notification
        user_is_mentor = str(bonafide.user.mentor.user.username) == str(request.user)
        user_is_advisor = str(bonafide.user.advisor.user.username) == str(request.user)
        # If staff is both mentor and advisor, update both statuses
        if (role == 'mentor' and user_is_mentor) or (role == 'advisor' and user_is_advisor):
            # If staff is both mentor and advisor for this student
            if user_is_mentor and user_is_advisor:
                bonafide.Mstatus = status
                bonafide.Astatus = status
                # Only set Hstatus if rejected
                if status == STATUS[2][0]:
                    bonafide.Hstatus = STATUS[2][0]
                Notification.objects.create(
                    student=bonafide.user,
                    message=f"Your Bonafide request was {status} by Mentor/Advisor"
                )
                bonafide.save()
                return redirect("staff_bonafides")
            # If only mentor
            if role == 'mentor' and user_is_mentor:
                bonafide.Mstatus = status
                if status == STATUS[2][0]:  # Rejected
                    bonafide.Astatus = STATUS[2][0]
                    bonafide.Hstatus = STATUS[2][0]
                Notification.objects.create(
                    student=bonafide.user,
                    message=f"Your Bonafide request was {bonafide.Mstatus} by Mentor"
                )
                bonafide.save()
                return redirect("staff_bonafides")
            # If only advisor
            if role == 'advisor' and user_is_advisor:
                bonafide.Astatus = status
                if bonafide.Mstatus == STATUS[0][0]:  # Pending
                    bonafide.Mstatus = bonafide.Astatus
                if status == STATUS[2][0]:
                    bonafide.Hstatus = STATUS[2][0]
                Notification.objects.create(
                    student=bonafide.user,
                    message=f"Your Bonafide request was {bonafide.Astatus} by Advisor"
                )
                bonafide.save()
                return redirect("staff_bonafides")
        if role == 'hod' and str(bonafide.user.hod.user.username) == str(request.user):
            if status == STATUS[1][0]:  # Approved
                bonafide.Mstatus = STATUS[1][0]
                bonafide.Astatus = STATUS[1][0]
                bonafide.Hstatus = STATUS[1][0]
            elif status == STATUS[2][0]:  # Rejected
                bonafide.Mstatus = STATUS[2][0]
                bonafide.Astatus = STATUS[2][0]
                bonafide.Hstatus = STATUS[2][0]
            Notification.objects.create(
                student=bonafide.user,
                message=f"Your Bonafide request was {status} by HOD"
            )
            bonafide.save()
            return redirect("hod_bonafide_view")
        bonafide.save()
        return redirect("hod_bonafide_view")
def forgot_password(request):
    message = None
    error_message = None
    if request.method == 'POST':
        email = request.POST.get('email')
        user_obj = None
        try:
            user_obj = Student.objects.get(user__email=email)
        except Student.DoesNotExist:
            try:
                user_obj = Staff.objects.get(email=email)
            except Staff.DoesNotExist:
                error_message = 'Email not registered.'
        if user_obj:
            otp = str(random.randint(100000, 999999))
            request.session['reset_email'] = email
            request.session['reset_otp'] = otp
            send_mail(
                'Your OTP Code',
                f'Your OTP code is {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            request.session['otp_sent'] = True
            return redirect('otp_verification')
    return render(request, 'auth/forgot_password.html', {'message': message, 'error_message': error_message})

def otp_verification(request):
    error_message = None
    success_message = None
    if request.session.get('otp_sent'):
        success_message = 'OTP has been sent to your registered email.'
        request.session.pop('otp_sent')
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('reset_otp')
        if entered_otp == session_otp:
            request.session['otp_verified'] = True
            return redirect('reset_password')
        else:
            error_message = 'Invalid OTP. Please try again.'
    return render(request, 'auth/otp_verification.html', {'error_message': error_message, 'success_message': success_message})

def reset_password(request):
    error_message = None
    if not request.session.get('otp_verified'):
        return redirect('forgot_password')
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password != confirm_password:
            error_message = 'Passwords do not match.'
        else:
            email = request.session.get('reset_email')
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            request.session.flush()
            return redirect('login')
    return render(request, 'auth/reset_password.html', {'error_message': error_message})

def student_timetable(request):
    # Delegate to the actual student timetable view implementation
    from .student_timetable_views import student_timetable as real_student_timetable
    return real_student_timetable(request)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def hod_action_od(request, id):
    if request.method == 'POST':
        od = OD.objects.get(id=id)
        action_status = request.POST.get('sts')
        role = request.POST.get('role')
        if role == 'mentor':
            od.Mstatus = action_status
            if action_status == STATUS[2][0]:  # Rejected
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
                od.AHstatus = STATUS[2][0]
        elif role == 'hod':
            if action_status == STATUS[1][0]:  # 'Approved'
                od.Mstatus = STATUS[1][0]
                od.Astatus = STATUS[1][0]
                od.Hstatus = STATUS[1][0]
                od.AHstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                od.Mstatus = STATUS[2][0]
                od.Astatus = STATUS[2][0]
                od.Hstatus = STATUS[2][0]
                od.AHstatus = STATUS[2][0]
        from .models import Notification
        Notification.objects.create(
            student=od.user,
            message=f"Your OD request was {action_status} by {'Mentor' if role == 'mentor' else 'HOD'}"
        )
        od.save()
        return redirect('hod_od_view')
    return redirect('hod_od_view')

@csrf_exempt
@login_required
def hod_action_leave(request, id):
    if request.method == 'POST':
        leave = LEAVE.objects.get(id=id)
        action_status = request.POST.get('sts')
        role = request.POST.get('role')
        if role == 'mentor':
            leave.Mstatus = action_status
            if action_status == STATUS[2][0]:  # Rejected
                leave.Astatus = STATUS[2][0]
                leave.Hstatus = STATUS[2][0]
                leave.AHstatus = STATUS[2][0]
        elif role == 'hod':
            if action_status == STATUS[1][0]:  # 'Approved'
                leave.Mstatus = STATUS[1][0]
                leave.Astatus = STATUS[1][0]
                leave.Hstatus = STATUS[1][0]
                leave.AHstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                leave.Mstatus = STATUS[2][0]
                leave.Astatus = STATUS[2][0]
                leave.Hstatus = STATUS[2][0]
                leave.AHstatus = STATUS[2][0]
        from .models import Notification
        Notification.objects.create(
            student=leave.user,
            message=f"Your Leave request was {action_status} by {'Mentor' if role == 'mentor' else 'HOD'}"
        )
        leave.save()
        return redirect('hod_leave_view')
    return redirect('hod_leave_view')

@csrf_exempt
@login_required
def hod_action_gatepass(request, id):
    if request.method == 'POST':
        gatepass = GATEPASS.objects.get(id=id)
        action_status = request.POST.get('sts')
        role = request.POST.get('role')
        if role == 'mentor':
            gatepass.Mstatus = action_status
            if action_status == STATUS[2][0]:  # Rejected
                gatepass.Astatus = STATUS[2][0]
                gatepass.Hstatus = STATUS[2][0]
        elif role == 'hod':
            if action_status == STATUS[1][0]:  # 'Approved'
                gatepass.Mstatus = STATUS[1][0]
                gatepass.Astatus = STATUS[1][0]
                gatepass.Hstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                gatepass.Mstatus = STATUS[2][0]
                gatepass.Astatus = STATUS[2][0]
                gatepass.Hstatus = STATUS[2][0]
        from .models import Notification
        Notification.objects.create(
            student=gatepass.user,
            message=f"Your Gatepass request was {action_status} by {'Mentor' if role == 'mentor' else 'HOD'}"
        )
        gatepass.save()
        return redirect('hod_gatepass_view')
    return redirect('hod_gatepass_view')

@csrf_exempt
@login_required
def hod_action_bonafide(request, id):
    if request.method == 'POST':
        bonafide = BONAFIDE.objects.get(id=id)
        action_status = request.POST.get('sts')
        role = request.POST.get('role')
        if role == 'mentor':
            bonafide.Mstatus = action_status
            if action_status == STATUS[2][0]:  # Rejected
                bonafide.Astatus = STATUS[2][0]
                bonafide.Hstatus = STATUS[2][0]
        elif role == 'hod':
            if action_status == STATUS[1][0]:  # 'Approved'
                bonafide.Mstatus = STATUS[1][0]
                bonafide.Astatus = STATUS[1][0]
                bonafide.Hstatus = STATUS[1][0]
            elif action_status == STATUS[2][0]:  # 'Rejected'
                bonafide.Mstatus = STATUS[2][0]
                bonafide.Astatus = STATUS[2][0]
                bonafide.Hstatus = STATUS[2][0]

        from .models import Notification
        Notification.objects.create(
            student=bonafide.user,
            message=f"Your Bonafide request was {action_status} by {'Mentor' if role == 'mentor' else 'HOD'}"
        )
        bonafide.save()
        return redirect('hod_bonafide_view')
    return redirect('hod_bonafide_view')

@login_required
def ahod_timetable(request):
    context = set_config(request)
    ahod = AHOD.objects.get(user=context['duser'])
    # Get department code for AHOD
    ahod_dept = ahod.user.department
    # Fetch timetable data for the department
    context['days'] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    context['periods'] = ['Period 1', 'Period 2', 'Period 3', 'Period 4', 'Period 5', 'Period 6', 'Period 7']
    context['table'] = {}  # Replace with actual timetable data
    context['my_table'] = {}  # Replace with actual personal timetable data
    if request.method == 'POST':
        # Save timetable data to the database
        Timetable.objects.filter(user=request.user).delete()  # Clear existing data
        for day in context['days']:
            for period in context['periods']:
                key = f"{day}_{period}"
                subject = request.POST.get(f"my_{key}", '')
                if subject:
                    Timetable.objects.create(user=request.user, day=day, period=period, subject=subject)
        messages.success(request, 'Timetable updated successfully!')

    # Retrieve timetable data from the database
    timetable_entries = Timetable.objects.filter(user=request.user)
    my_table = {f"{entry.day}_{entry.period}": entry.subject for entry in timetable_entries}
    context['my_table'] = my_table

    return render(request, 'ahod/timetable.html', context)

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
from django.shortcuts import render
from .models import Student, OD, LEAVE
from django.db.models import Q
@login_required
def student_details(request):
    staff = Staff.objects.get(user=request.user)
    is_advisor = (getattr(staff, 'position', None) == 4 or getattr(staff, 'position2', None) == 4)
    
    # Get all students related to this staff member (as advisor, a_advisor, mentor, or teaching staff)
    students = Student.objects.filter(
        Q(advisor=staff) | Q(a_advisor=staff) | Q(mentor=staff) | Q(teaching_staffs=staff)
    ).distinct().order_by('roll')
    
    student_data = []
    for student in students:
        od_qs = OD.objects.filter(user=student)
        leave_qs = LEAVE.objects.filter(user=student)
        od_details = [f"{od.sub} ({od.start.strftime('%Y-%m-%d')} - {od.end.strftime('%Y-%m-%d')}) [{od.status}]" for od in od_qs]
        def get_final_leave_status(leave):
            if 'Rejected' in [leave.Astatus, leave.Mstatus, leave.Hstatus, leave.AHstatus]:
                return 'Rejected'
            elif 'Pending' in [leave.Astatus, leave.Mstatus, leave.Hstatus, leave.AHstatus]:
                return 'Pending'
            elif leave.Astatus == 'Approved' and leave.Mstatus == 'Approved' and leave.Hstatus == 'Approved' and leave.AHstatus == 'Approved':
                return 'Approved'
            else:
                return 'Pending'

        leave_details = [f"{leave.sub} ({leave.start.strftime('%Y-%m-%d')} - {leave.end.strftime('%Y-%m-%d')}) [{get_final_leave_status(leave)}]" for leave in leave_qs]
        student_data.append({
            'id': student.id,
            'roll_no': student.roll,
            'name': student.user.get_full_name(),
            'email': student.user.email,
            'department': student.department.name if student.department else 'N/A',
            'mobile': student.mobile,
            'od_details': od_details,  # Pass as list for correct count
            'leave_details': leave_details,  # Pass as list for correct count
            'address': student.address,
            'dob': student.dob.strftime('%Y-%m-%d') if student.dob else '',
            'gender': getattr(student, 'gender', ''),
            'father_name': getattr(student, 'father_name', ''),
            'mother_name': getattr(student, 'mother_name', ''),
            'community': getattr(student, 'community', ''),
            'religion': getattr(student, 'religion', ''),
            'nationality': getattr(student, 'nationality', ''),
        })
    duser = getattr(request.user, 'staff', None)
    return render(request, 'staff/student_details.html', {
        'students': student_data,
        'duser': duser,
    })

from django.shortcuts import render, get_object_or_404
from .models import Student, OD, LEAVE, GATEPASS, BONAFIDE

def view_student_details(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    # Add roll_no, email, gender, and mentor_name aliases for template compatibility
    student.roll_no = student.roll
    student.email = student.user.email if hasattr(student, 'user') and hasattr(student.user, 'email') else ''
    student.gender = student.user.gender if hasattr(student, 'user') and hasattr(student.user, 'gender') else student.gender if hasattr(student, 'gender') else ''
    student.mentor_name = student.mentor.name if student.mentor and hasattr(student.mentor, 'name') else ''
    
    # Add od_details, leave_details, gatepass_details, bonafide_details for template
    student.od_details = list(OD.objects.filter(user=student))
    student.leave_details = list(LEAVE.objects.filter(user=student))
    student.gatepass_details = list(GATEPASS.objects.filter(user=student))
    student.bonafide_details = list(BONAFIDE.objects.filter(user=student))
    
    # Add advisor_name for template
    student.advisor_name = student.advisor.name if student.advisor and hasattr(student.advisor, 'name') else ''

    # Check if the logged-in staff member has a relationship with this student
    is_advisor = False
    can_edit = False
    if request.user.is_authenticated and hasattr(request.user, 'staff'):
        staff = request.user.staff
        # Check if staff is related to this student (advisor, a_advisor, mentor, or teaching staff)
        from django.db.models import Q
        is_related = Student.objects.filter(
            Q(id=student_id) & (Q(advisor=staff) | Q(a_advisor=staff) | Q(mentor=staff) | Q(teaching_staffs=staff))
        ).exists()
        
        # Allow editing if staff is related to the student
        can_edit = is_related
        
        # Keep is_advisor for backward compatibility (specifically for position 4)
        is_advisor = (getattr(staff, 'position2', None) == 4 or getattr(staff, 'position', None) == 4) and is_related

    # Handle POST for editing
    if request.method == 'POST' and can_edit:
        gender = request.POST.get('gender')
        father_name = request.POST.get('father_name', '')
        mother_name = request.POST.get('mother_name', '')
        community = request.POST.get('community', '')
        religion = request.POST.get('religion', '')
        nationality = request.POST.get('nationality', '')
        other_nationality = request.POST.get('other_nationality', '')
        # If nationality is 'Other', use the text field value
        if nationality == 'Other' and other_nationality:
            nationality = other_nationality
        # Always update all fields, even if blank
        student.gender = gender
        student.father_name = father_name
        student.mother_name = mother_name
        student.community = community
        student.religion = religion
        student.nationality = nationality
        student.save()
        # If gender is on user, update user too
        if hasattr(student.user, 'gender'):
            student.user.gender = gender
            student.user.save()
        # Redirect to self to avoid resubmission and always show updated data
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        return HttpResponseRedirect(reverse('view_student_details', args=[student_id]))
    # Pass duser for sidebar logic
    duser = getattr(request.user, 'staff', None)
    return render(request, 'staff/view_student_details.html', {
        'student': student,
        'is_advisor': can_edit,  # Use can_edit flag to show/hide edit button
        'duser': duser,
    })

def view_student_leave_details(request, student_id):
    # TODO: Implement logic to show leave details for a student
    from django.shortcuts import render
    # leave_details = ... # fetch leave details for student_id
    return render(request, 'staff/student_leave_details.html', {'student_id': student_id})


