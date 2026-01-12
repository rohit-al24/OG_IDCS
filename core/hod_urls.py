from django.urls import path
from .views import hod_sports_od_view, hod_sports_od_action

urlpatterns = [
    # ... any other HOD urls can go here
    path('sports-od/approval/', hod_sports_od_view, name='hod_sports_od_view'),
    path('sports-od/action/<int:player_id>/', hod_sports_od_action, name='hod_sports_od_action'),
]
