
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class PathPilotMap(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	role = models.CharField(max_length=32)
	title = models.CharField(max_length=255)
	created_at = models.DateTimeField(auto_now_add=True)
	plan_json = models.JSONField()

	def __str__(self):
		return f"{self.title} ({self.user.username})"
