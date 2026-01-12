from django.urls import path, include
from .timetable_views import staff_timetable
from .student_timetable_views import student_timetable
from .views import *
from .views import gatepass_scanner_view
from .profile_views import staff_profile, hod_profile
from .view_mentees import view_mentees, my_mentees
from django.urls import path, include
from .views import principal_dashboard
from .ahod_actions import ahod_action_od
from .ahod_actions_leave import ahod_action_leave
from .timetable_views import hod_timetable
from django.shortcuts import render
from .models import Department
from django.contrib.auth import views as auth_views
from core.timetable_views import get_department_subjects


def principal_department(request):
    
    departments = Department.objects.all()
    return render(request, 'principal/department.html', {'departments': departments})

urlpatterns = [
    # Add these new includes
    path('pet/', include('core.pet_urls')),
    path('hod/', include('core.hod_urls')),
    path('staff/certificates/', staff_certificates, name='staff_certificates'),
    path('student/certificate/upload/', certificate_upload_view, name='certificate_upload'),
    path('student/recent-notifications/', recent_notifications_api, name='recent_notifications_api'),
    path('student/od/history/', student_od_history, name='student_od_history'),
    path('student/leave/history/', student_leave_history, name='student_leave_history'),
    path('student/bonafide/history/', student_bonafide_history, name='student_bonafide_history'),
    path('student/gatepass/history/', student_gatepass_history, name='student_gatepass_history'),
    path('staff/my_class/', my_class_students, name='staff_my_class'),
    path("", home, name='home'),
    path('student/gatepass/scan/', process_gatepass_qr_scan, name='process_gatepass_qr_scan'),
    path("notifications/", notifications_view, name="notifications_view"),
    path("notifications/delete_all/", delete_all_student_notifications, name="delete_all_student_notifications"),
    path("profile/", student_profile, name='student_profile'),
    path("staff/profile/", staff_profile, name='staff_profile'),
    path("hod/profile/", hod_profile, name='hod_profile'),
    path("od/",od,name='od'),
    path("od/upload_proof_od/<int:id>",upload_proof_od,name='proof_od'),
    path("leave/",leave,name='leave'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('otp-verification/', otp_verification, name='otp_verification'),
    path('reset-password/', reset_password, name='reset_password'),
    path("leave/upload_proof_od/<int:id>",upload_proof_leave,name='proof_leave'),
    path("gatepass/",gatepass,name='gatepass'),
    path("feedback",student_feedback,name='student_feedback'),
    path('bonafide/', bonafide_view, name='bonafide'),
    path('dash/', dash, name='dash'),
    path("dash/", ahod_dash, name="ahod_dash"),
    path('student/timetable/', student_timetable, name='student_timetable'),
    path('circular/<int:pk>/', circular_detail, name='circular_detail'),
    path("ahod/", include("core.ahod_urls")),
    path('hod/notifications/delete_all/', delete_all_hod_notifications, name='delete_all_hod_notifications'),
    path('hod/notifications/history/', hod_notification_history, name='hod_notification_history'),
    path('student/notifications/delete_all/', delete_all_student_notifications, name='delete_all_student_notifications'),
    path('staff/notifications/delete_all/', delete_all_staff_notifications, name='delete_all_staff_notifications'),
    path('hod/notifications/delete_all/', delete_all_notifications, name='delete_all_notifications'),
    path('hod/notifications/history/', ahod_notification_history, name='hod_notification_history'),
    path('hod/staff-list/', staff_list, name='staff_list'),
    path('hod/staff/<int:staff_id>/mentees/', view_mentees, name='view_mentees'),
    path('hod/my-mentees/', my_mentees, name='my_mentees'),


]

urlpatterns += [
    path('advisor/student/<int:student_id>/od_status/', advisor_student_od_status, name='advisor_student_od_status'),
    path('advisor/student/<int:student_id>/leave_status/', advisor_student_leave_status, name='advisor_student_leave_status'),
    path('advisor/student/<int:student_id>/gatepass_status/', advisor_student_gatepass_status, name='advisor_student_gatepass_status'),
    path('advisor/student/<int:student_id>/bonafide_status/', advisor_student_bonafide_status, name='advisor_student_bonafide_status'),
    path("ahods/check", ahod_od_view, name='ahod_od_view'),
    path("ahleaves/check", ahod_leave_view, name='ahod_leave_view'),
    path("ahods/action/<int:id>", ahod_action_od, name="ahod_action_od"),
    path('gatepass/scan/', scan_gatepass_qr, name='scan_gatepass_qr'),
    path('gatepass/scanner/', gatepass_scanner_view, name='gatepass_scanner'),
    path("ahleaves/action/<int:id>", ahod_action_leave, name="ahod_action_leave"),

]
# staff

urlpatterns += [
    path("ods/check",staff_od_view,name='staff_od_view'),
    path("ods/action/<int:id>",staff_action_od,name='staff_action_od'),
    path("leaves/check",staff_leave_view,name='staff_leave_view'),
    path("leaves/action/<int:id>",staff_action_leave,name='staff_action_leave'),
    path("gatepasss/check",staff_gatepass_view,name='staff_gatepass_view'),
    path("gatepass/action/<int:id>",staff_action_gatepass,name='staff_action_gatepass'),
    path("bonafide/action/<int:id>", staff_action_bonafide, name="staff_action_bonafide"),
    path("bonafides/", staff_bonafides, name="staff_bonafides"),
    path("staff/notifications/", staff_notifications_view, name="staff_notifications"),
    path("timetable/", staff_timetable, name="staff_timetable"),
# ...existing code...
    path("my_class_students/", my_class_students, name="my_class_students"),
    path("staff/attendance/", staff_attendance_view, name="staff_attendance"),
    path("student/attendance/", student_attendance_view, name="student_attendance"),

    # Principal URLs
    path('principal/dashboard/', principal_dashboard, name='principal_dashboard'),
    path('principal/department/', principal_department, name='principal_department'),
    
    path('principal/department/<int:dept_id>/students/', principal_department_students, name='principal_department_students'),
    path('principal/department/<int:dept_id>/staff/', principal_department_staff, name='principal_department_staff'),


    # Staff student details from ahod branch
    path('staff/student_details/', student_details, name='student_details'),
    path('staff/student/<int:student_id>/', view_student_details, name='view_student_details'),

    path('staff/student/<int:student_id>/leave_details/', view_student_leave_details, name='view_student_leave_details'),
]
# hod

urlpatterns += [
    path("hods/check", hod_od_view, name='hod_od_view'),
    path("hods/action/<int:id>", hod_action_od, name="hod_action_od"),
    path("hleaves/action/<int:id>", hod_action_leave, name="hod_action_leave"),
    path("hgatepass/action/<int:id>", hod_action_gatepass, name="hod_action_gatepass"),
    path("hbonafide/action/<int:id>", hod_action_bonafide, name="hod_action_bonafide"),
    path("hbonafide/", hod_bonafide_view, name="hod_bonafide_view"),
    path('hod/notifications/', hod_notification_history, name='hod_notification_history'),
    path("hleaves/check", hod_leave_view, name="hod_leave_view"),
    path("hgatepass/check", hod_gatepass_view, name="hod_gatepass_view"),
]


# AHOD
urlpatterns += [
    path("bonafide-hod/", ahod_bonafide_hod, name="ahod_bonafide_hod"),
    path("gatepass-hod/", ahod_gatepass_hod, name="ahod_gatepass_hod"),
]

urlpatterns += [
    path("ahod/notifications/", ahod_notification_history, name="ahod_notification_history"),
]

# auth
urlpatterns += [
    path("login/", login_user, name='login'),
    path("logout/", logout_user, name='logout')
]

urlpatterns += [
    path('ahod/timetable/', ahod_timetable, name='ahod_timetable'),
]


# API

# R & D

# Placement



urlpatterns += [
    path("hod/timetable/", hod_timetable, name="hod_timetable"),
]


urlpatterns += [
    path('password_change/', otp_verification, name='password_change'),
]


urlpatterns += [
    path('get-department-subjects/<int:department_id>/', get_department_subjects, name='get_department_subjects'),
]




