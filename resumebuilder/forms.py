# resumebuilder/forms.py
from django import forms
from .models import Resume, Skill, Education, Achievement, Project, Social, Language

class ResumeForm(forms.ModelForm):
	class Meta:
		model = Resume
		fields = [
			'name', 'email', 'phone', 'img', 'role', 'bio', 'template_id',
			'declaration_text', 'declaration_signature', 'declaration_place', 'declaration_date'
		]
		widgets = {
			'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
			'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
			'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number', 'type': 'tel', 'pattern': '[0-9]*'}),
			'img': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
			'role': forms.TextInput(attrs={'class': 'form-control'}),
			'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
			'template_id': forms.NumberInput(attrs={'class': 'form-control'}),
			'declaration_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
			'declaration_signature': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
			'declaration_place': forms.TextInput(attrs={'class': 'form-control'}),
			'declaration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
		}

class SkillForm(forms.ModelForm):
	class Meta:
		model = Skill
		fields = ['name', 'level']

	def __init__(self, *args, **kwargs):
		self.resume = kwargs.pop('resume', None)
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.resume:
			instance.resume = self.resume
		if commit:
			instance.save()
		return instance

class EducationForm(forms.ModelForm):
	class Meta:
		model = Education
		fields = ['institution', 'degree', 'field', 'start_year', 'end_year']

	def __init__(self, *args, **kwargs):
		self.resume = kwargs.pop('resume', None)
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.resume:
			instance.resume = self.resume
		if commit:
			instance.save()
		return instance

class AchievementForm(forms.ModelForm):
	class Meta:
		model = Achievement
		fields = ['title', 'description', 'date']

	def __init__(self, *args, **kwargs):
		self.resume = kwargs.pop('resume', None)
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.resume:
			instance.resume = self.resume
		if commit:
			instance.save()
		return instance

class ProjectForm(forms.ModelForm):
	class Meta:
		model = Project
		fields = ['name', 'description', 'link']

	def __init__(self, *args, **kwargs):
		self.resume = kwargs.pop('resume', None)
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.resume:
			instance.resume = self.resume
		if commit:
			instance.save()
		return instance

class SocialForm(forms.ModelForm):
	class Meta:
		model = Social
		fields = ['platform', 'url']

	def __init__(self, *args, **kwargs):
		self.resume = kwargs.pop('resume', None)
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.resume:
			instance.resume = self.resume
		if commit:
			instance.save()
		return instance

class LanguageForm(forms.ModelForm):
	class Meta:
		model = Language
		fields = ['name', 'proficiency']

	def __init__(self, *args, **kwargs):
		self.resume = kwargs.pop('resume', None)
		super().__init__(*args, **kwargs)

	def save(self, commit=True):
		instance = super().save(commit=False)
		if self.resume:
			instance.resume = self.resume
		if commit:
			instance.save()
		return instance