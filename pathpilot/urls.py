from django.urls import path
from . import views

urlpatterns = [
	path("", views.cp, name="pathpilot"),
	path("course_map/", views.course_map, name="course_map"),
	path("map_history/", views.map_history, name="map_history"),
	path("map_detail/<int:map_id>/", views.map_detail, name="map_detail"),
	path("save_map/", views.save_map, name="save_map"),
]
