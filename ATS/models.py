
from django.db import models
from core.models import Student

class UploadedResume(models.Model):
	student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='uploaded_resumes')
	file = models.FileField(upload_to='resumes/')
	extracted_text = models.TextField()
	uploaded_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"{self.student} - {self.file.name}"
class LEAVE(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='leaves')
    reason = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, default='Pending')  # Add status field

    def __str__(self):
        return f"{self.student} - {self.status}"

# Stores the analysis results for a resume
class ResumeAnalysis(models.Model):
    resume = models.ForeignKey(UploadedResume, on_delete=models.CASCADE, related_name='analyses')
    results = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.resume} at {self.created_at}" 
