from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_feedback_form, name='feed360_create'),
    path('staff/<int:staff_id>/results/', views.results_for_staff, name='feed360_staff_results'),
    path('', views.list_active_forms, name='feed360_index'),
    path('<int:form_id>/fill/', views.fill_feedback_form, name='feed360_fill'),
    path('hod/forms/', views.hod_list_forms, name='feed360_hod_list_forms'),
    path('hod/forms/<int:form_id>/deactivate/', views.hod_deactivate_form, name='feed360_hod_deactivate_form'),
    path('hod/forms/<int:form_id>/results/', views.hod_results_form, name='feed360_hod_results_form'),
    path('hod/staff-feedback/', views.hod_staff_feedback_results, name='feed360_hod_staff_feedback_results'),
    path('hod/view-comments/<int:staff_id>/<int:form_id>/<int:question_id>/', views.hod_view_comments, name='feed360_hod_view_comments'),
    path('hod/view-comments-all/<int:staff_id>/<int:form_id>/', views.hod_view_comments_all, name='feed360_hod_view_comments_all'),
    path('staff/my-results/', views.staff_my_results, name='feed360_staff_my_results'),
    path('hod/view-comments-all-custom/<str:custom_staff_name>/<int:form_id>/', views.hod_view_comments_all_custom, name='feed360_hod_view_comments_all_custom'),
]
