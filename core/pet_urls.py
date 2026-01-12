from django.urls import path
from .views import pet_dashboard, pet_sports_od_apply, pet_sports_od_status, get_student_details

urlpatterns = [
    path('dashboard/', pet_dashboard, name='pet_dashboard'),
    path('sports-od/apply/', pet_sports_od_apply, name='pet_sports_od_apply'),
    path('sports-od/status/', pet_sports_od_status, name='pet_sports_od_status'),
    # Update this URL to accept the user_id
    path('api/get-student-details/<str:user_id>/', get_student_details, name='get_student_details'),
]
