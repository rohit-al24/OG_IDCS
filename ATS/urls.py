from django.urls import path
from . import views

app_name = 'ATS'

urlpatterns = [
	path('dashboard/', views.ats_dashboard, name='ats_dashboard'),
	path('upload/', views.upload_resume, name='upload_resume'),
	path('<int:resume_id>/preview/', views.resume_preview, name='resume_preview'),
	path('<int:resume_id>/analysis/', views.resume_analysis, name='resume_analysis'),
	path('<int:resume_id>/loading/', views.resume_loading, name='resume_loading'),
]
