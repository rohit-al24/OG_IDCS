from django.urls import path
from .views import *

urlpatterns = [
    path("dash/", ahod_dash, name="ahod_dash"),
    path("bonafide-hod/", ahod_bonafide_hod, name="ahod_bonafide_hod"),
    path("gatepass-hod/", ahod_gatepass_hod, name="ahod_gatepass_hod"),
]
