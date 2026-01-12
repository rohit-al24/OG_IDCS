# resumebuilder/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def resume_image_upload_path(instance, filename):
	return f'resume/{instance.user.id}/{filename}'

class Resume(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
	img = models.ImageField(upload_to=resume_image_upload_path, blank=True, null=True)
	name = models.CharField(max_length=100, blank=True, null=True)
	email = models.EmailField(max_length=254, blank=True, null=True)
	phone = models.CharField(max_length=20, blank=True, null=True)
	role = models.CharField(max_length=100, blank=True)
	bio = models.TextField(blank=True)
	template_id = models.IntegerField(default=1)
	created_at = models.DateTimeField(default=timezone.now)
	declaration_text = models.TextField(blank=True, null=True)
	declaration_signature = models.ImageField(upload_to='resume/signatures/', blank=True, null=True)
	declaration_place = models.CharField(max_length=100, blank=True, null=True)
	declaration_date = models.DateField(blank=True, null=True)
	
	@property
	def profile_pic_url(self):
		if self.img and self.img.name:
			return self.img.url
		return '/static/images/default_profile.png'

	def __str__(self):
		return f"{self.user.username} - {self.role}"

	def get_skills(self):
		return self.skills.all()

	def get_education(self):
		return self.education.all()

	def get_achievements(self):
		return self.achievements.all()

	def get_projects(self):
		return self.projects.all()

	def get_socials(self):
		return self.socials.all()

	def get_languages(self):
		return self.languages.all()

class Skill(models.Model):
	resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='skills')
	name = models.CharField(max_length=100)
	level = models.CharField(max_length=50, blank=True)

	def __str__(self):
		return self.name

class Education(models.Model):
	resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='education')
	institution = models.CharField(max_length=200)
	degree = models.CharField(max_length=100)
	field = models.CharField(max_length=100, blank=True)
	start_year = models.CharField(max_length=4, blank=True)
	end_year = models.CharField(max_length=4, blank=True)
	grade = models.CharField(max_length=50, blank=True)

	def __str__(self):
		return f"{self.degree} at {self.institution}"

class Achievement(models.Model):
	resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='achievements')
	title = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	date = models.DateField(blank=True, null=True)

	def __str__(self):
		return self.title

class Project(models.Model):
	resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='projects')
	name = models.CharField(max_length=200)
	description = models.TextField(blank=True)
	link = models.URLField(blank=True)

	def __str__(self):
		return self.name

class Social(models.Model):
	resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='socials')
	platform = models.CharField(max_length=100)
	url = models.URLField()

	def __str__(self):
		return self.platform

class Language(models.Model):
	resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='languages')
	name = models.CharField(max_length=100)
	proficiency = models.CharField(max_length=100, blank=True)

	def __str__(self):
		return self.name