from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

# Explicit imports for Student, Staff
from core.models import Student, Staff
# Try to import Subject, fallback if not found
try:
	from core.models import SemesterSubject as Subject
except ImportError:
	class Subject(models.Model):
		name = models.CharField(max_length=100)
		code = models.CharField(max_length=20)
		def __str__(self):
			return f"{self.code} - {self.name}"


class FeedbackForm(models.Model):
	title = models.CharField(max_length=200)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	department = models.CharField(max_length=50)
	year = models.PositiveIntegerField()
	section = models.CharField(max_length=10)
	created_at = models.DateTimeField(auto_now_add=True)
	active = models.BooleanField(default=True)
	# New fields for staff linking
	staff_name = models.CharField(max_length=100, blank=True, null=True, help_text="Selected staff name for feedback linking")
	staff_name_other = models.CharField(max_length=100, blank=True, null=True, help_text="Custom staff name if 'Others' selected")

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.title} ({self.department}-{self.year}-{self.section})"

ANSWER_TYPE_CHOICES = [
	('stars', 'Stars'),
	('text', 'Text'),
	('both', 'Stars & Text'),
]


class FeedbackQuestion(models.Model):
	form = models.ForeignKey(FeedbackForm, on_delete=models.CASCADE, related_name='questions')
	text = models.CharField(max_length=300)
	answer_type = models.CharField(max_length=10, choices=ANSWER_TYPE_CHOICES)
	# subject: FK if Subject exists, else CharField
	subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
	# If no Subject model, fallback to CharField
	subject_text = models.CharField(max_length=100, blank=True, null=True)
	# New fields for staff linking
	staff_name = models.CharField(max_length=100, blank=True, null=True, help_text="Selected staff name for feedback linking")
	staff_name_other = models.CharField(max_length=100, blank=True, null=True, help_text="Custom staff name if 'Others' selected")

	class Meta:
		ordering = ['form', 'id']

	def __str__(self):
		return f"Q: {self.text} ({self.answer_type})"

class FeedbackResponse(models.Model):
	form = models.ForeignKey(FeedbackForm, on_delete=models.CASCADE)
	question = models.ForeignKey(FeedbackQuestion, on_delete=models.CASCADE)
	student = models.ForeignKey(Student, on_delete=models.CASCADE)
	staff = models.ForeignKey(Staff, on_delete=models.CASCADE, null=True, blank=True)
	rating = models.IntegerField(null=True, blank=True)
	comment = models.TextField(null=True, blank=True)
	sentiment_label = models.CharField(max_length=16, blank=True, null=True)  # Store sentiment at submission
	submitted_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-submitted_at']

	def __str__(self):
		return f"{self.student} -> {self.staff} [{self.question}]"

class FeedbackAggregate(models.Model):
	form = models.ForeignKey(FeedbackForm, on_delete=models.CASCADE)
	staff = models.ForeignKey(Staff, on_delete=models.CASCADE)
	subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
	avg_rating = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
	sentiment_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
	last_computed = models.DateTimeField(default=timezone.now)
	avg_star_rating = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
	avg_sentiment_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
	sentiment_distribution = models.JSONField(null=True, blank=True)
	aspect_scores = models.JSONField(null=True, blank=True)

	class Meta:
		ordering = ['-last_computed']

	def __str__(self):
		return f"Aggregate: {self.staff} {self.subject} {self.avg_rating}"
