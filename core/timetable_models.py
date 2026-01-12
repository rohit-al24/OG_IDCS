from django.db import models
from .models import Staff

class StaffTimeTable(models.Model):
    staff = models.OneToOneField(Staff, on_delete=models.CASCADE, related_name='timetable')
    data = models.JSONField(default=dict)  # Main timetable
    my_timetable_data = models.JSONField(default=dict)  # For 'My Timetable'

    def __str__(self):
        return f"Timetable for {self.staff.name}"
