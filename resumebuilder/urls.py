# resumebuilder/urls.py
from django.urls import path
from . import views

app_name = 'resumebuilder'

urlpatterns = [
    path('rb/', views.rb, name='rb'),
    path('resume/<int:id>/edit/', views.create_resume, name='create_resume'),
    path('resume/<int:id>/templates/', views.resume_templates, name='resume_templates'),
    path('resume/<int:id>/delete/', views.delete_resume, name='delete_resume'),

    # Section CRUD (AJAX/HTMX)
    path('resume/<int:id>/skill/create/', views.create_skill, name='create_skill'),
    path('resume/<int:id>/skill/<int:skill_id>/delete/', views.delete_skill, name='delete_skill'),
    path('resume/<int:id>/edu/create/', views.create_edu, name='create_edu'),
    path('resume/<int:id>/edu/<int:edu_id>/delete/', views.delete_edu, name='delete_edu'),
    path('resume/<int:id>/ach/create/', views.create_ach, name='create_ach'),
    path('resume/<int:id>/ach/<int:ach_id>/delete/', views.delete_ach, name='delete_ach'),
    path('resume/<int:id>/pro/create/', views.create_pro, name='create_pro'),
    path('resume/<int:id>/pro/<int:pro_id>/delete/', views.delete_pro, name='delete_pro'),
    path('resume/<int:id>/soc/create/', views.create_soc, name='create_soc'),
    path('resume/<int:id>/soc/<int:soc_id>/delete/', views.delete_soc, name='delete_soc'),
    path('resume/<int:id>/lang/create/', views.create_lang, name='create_lang'),
    path('resume/<int:id>/lang/<int:lang_id>/delete/', views.delete_lang, name='delete_lang'),
]
