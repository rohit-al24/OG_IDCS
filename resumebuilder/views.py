
# resumebuilder/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Resume, Skill, Education, Achievement, Project, Social, Language
from .forms import ResumeForm, SkillForm, EducationForm, AchievementForm, ProjectForm, SocialForm, LanguageForm
from core.models import Student

@login_required
@require_POST
def delete_resume(request, id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	resume.delete()
	return redirect('resumebuilder:rb')

def is_student(user):
	return Student.objects.filter(user=user).exists()

@login_required
def rb(request):
	if not is_student(request.user):
		return HttpResponseForbidden()
	resumes = Resume.objects.filter(user=request.user)
	if request.method == 'POST':
		resume = Resume.objects.create(user=request.user, role='Student', bio='', template_id=1)
		return redirect('resumebuilder:create_resume', id=resume.id)
	return render(request, 'resumebuilder/rb.html', {'resumes': resumes})

@login_required
def create_resume(request, id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	if not is_student(request.user):
		return HttpResponseForbidden()
	if request.method == 'POST':
		form = ResumeForm(request.POST, request.FILES, instance=resume)
		action = request.POST.get('action')
		if action == 'save_personal_info':
			if form.is_valid():
				form.save()
				return redirect('resumebuilder:create_resume', id=resume.id)
			# else: fall through to render with errors
		else:
			if form.is_valid():
				resume_obj = form.save(commit=False)
				resume_obj.user = request.user
				resume_obj.save()
				# Save skills
				resume_obj.skills.all().delete()
				skills = request.POST.getlist('skills[]')
				for skill_name in skills:
					if skill_name.strip():
						Skill.objects.create(resume=resume_obj, name=skill_name.strip())
				# Save education
				resume_obj.education.all().delete()
				edu_institution = request.POST.getlist('edu_institution[]')
				edu_degree = request.POST.getlist('edu_degree[]')
				edu_field = request.POST.getlist('edu_field[]')
				edu_start_year = request.POST.getlist('edu_start_year[]')
				edu_end_year = request.POST.getlist('edu_end_year[]')
				edu_grade = request.POST.getlist('edu_grade[]')
				for i in range(len(edu_institution)):
					if edu_institution[i].strip():
						Education.objects.create(
							resume=resume_obj,
							institution=edu_institution[i].strip(),
							degree=edu_degree[i].strip() if i < len(edu_degree) else '',
							field=edu_field[i].strip() if i < len(edu_field) else '',
							start_year=edu_start_year[i].strip() if i < len(edu_start_year) else '',
							end_year=edu_end_year[i].strip() if i < len(edu_end_year) else '',
							grade=edu_grade[i].strip() if i < len(edu_grade) else '',
						)
				# Save achievements
				import datetime
				resume_obj.achievements.all().delete()
				ach_title = request.POST.getlist('ach_title[]')
				ach_description = request.POST.getlist('ach_description[]')
				ach_date = request.POST.getlist('ach_date[]')
				for i in range(len(ach_title)):
					if ach_title[i].strip():
						# Validate and parse date
						ach_date_val = None
						if i < len(ach_date):
							date_str = ach_date[i].strip()
							if date_str:
								try:
									ach_date_val = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
								except Exception:
									ach_date_val = None
						Achievement.objects.create(
							resume=resume_obj,
							title=ach_title[i].strip(),
							description=ach_description[i].strip() if i < len(ach_description) else '',
							date=ach_date_val,
						)
				# Save projects
				resume_obj.projects.all().delete()
				pro_name = request.POST.getlist('pro_name[]')
				pro_description = request.POST.getlist('pro_description[]')
				pro_link = request.POST.getlist('pro_link[]')
				for i in range(len(pro_name)):
					if pro_name[i].strip():
						Project.objects.create(
							resume=resume_obj,
							name=pro_name[i].strip(),
							description=pro_description[i].strip() if i < len(pro_description) else '',
							link=pro_link[i].strip() if i < len(pro_link) else '',
						)
				# Save socials
				resume_obj.socials.all().delete()
				soc_platform = request.POST.getlist('soc_platform[]')
				soc_url = request.POST.getlist('soc_url[]')
				for i in range(len(soc_platform)):
					if soc_platform[i].strip() and i < len(soc_url):
						Social.objects.create(
							resume=resume_obj,
							platform=soc_platform[i].strip(),
							url=soc_url[i].strip(),
						)
				# Save languages
				resume_obj.languages.all().delete()
				lang_name = request.POST.getlist('lang_name[]')
				lang_proficiency = request.POST.getlist('lang_proficiency[]')
				for i in range(len(lang_name)):
					if lang_name[i].strip():
						Language.objects.create(
							resume=resume_obj,
							name=lang_name[i].strip(),
							proficiency=lang_proficiency[i].strip() if i < len(lang_proficiency) else '',
						)
				return redirect('resumebuilder:create_resume', id=resume_obj.id)
	else:
		form = ResumeForm(instance=resume)

	context = {
		'resume': resume,
		'form': form,
		'skills': resume.get_skills(),
		'education': resume.get_education(),
		'achievements': resume.get_achievements(),
		'projects': resume.get_projects(),
		'socials': resume.get_socials(),
		'languages': resume.get_languages(),
		'skill_form': SkillForm(),
		'edu_form': EducationForm(),
		'ach_form': AchievementForm(),
		'pro_form': ProjectForm(),
		'soc_form': SocialForm(),
		'lang_form': LanguageForm(),
	}
	return render(request, 'resumebuilder/create.html', context)

@login_required
def resume_templates(request, id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	if not is_student(request.user):
		return HttpResponseForbidden()
	if request.method == 'POST':
		template_id = request.POST.get('template_id')
		if template_id:
			resume.template_id = int(template_id)
			resume.save()
	# Fetch student details
	student = None
	email = ''
	phone = ''
	try:
		student = Student.objects.get(user=request.user)
		email = request.user.email
		phone = student.mobile if student.mobile else ''
	except Student.DoesNotExist:
		pass
	context = {
		'resume': resume,
		'skills': resume.get_skills(),
		'education': resume.get_education(),
		'achievements': resume.get_achievements(),
		'projects': resume.get_projects(),
		'socials': resume.get_socials(),
		'languages': resume.get_languages(),
		'student_email': email,
		'student_phone': phone,
	}
	return render(request, 'resumebuilder/resume_template.html', context)

# Section CRUD views (AJAX/HTMX)
@login_required
def create_skill(request, id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	if request.method == 'POST':
		form = SkillForm(request.POST, resume=resume)
		if form.is_valid():
			form.save()
	skills_html = render_to_string('resumebuilder/partial/skills.html', {'skills': resume.get_skills()})
	return JsonResponse({'html': skills_html})

@login_required
def delete_skill(request, id, skill_id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	skill = get_object_or_404(Skill, id=skill_id, resume=resume)
	skill.delete()
	skills_html = render_to_string('resumebuilder/partial/skills.html', {'skills': resume.get_skills()})
	return JsonResponse({'html': skills_html})

@login_required
def create_edu(request, id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	if request.method == 'POST':
		form = EducationForm(request.POST, resume=resume)
		if form.is_valid():
			form.save()
	edu_html = render_to_string('resumebuilder/partial/edu.html', {'education': resume.get_education()})
	return JsonResponse({'html': edu_html})

@login_required
def delete_edu(request, id, edu_id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	edu = get_object_or_404(Education, id=edu_id, resume=resume)
	edu.delete()
	edu_html = render_to_string('resumebuilder/partial/edu.html', {'education': resume.get_education()})
	return JsonResponse({'html': edu_html})

@login_required
def create_ach(request, id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	if request.method == 'POST':
		form = AchievementForm(request.POST, resume=resume)
		if form.is_valid():
			form.save()
	ach_html = render_to_string('resumebuilder/partial/ach.html', {'achievements': resume.get_achievements()})
	return JsonResponse({'html': ach_html})

@login_required
def delete_ach(request, id, ach_id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	ach = get_object_or_404(Achievement, id=ach_id, resume=resume)
	ach.delete()
	ach_html = render_to_string('resumebuilder/partial/ach.html', {'achievements': resume.get_achievements()})
	return JsonResponse({'html': ach_html})

@login_required
def create_pro(request, id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	if request.method == 'POST':
		form = ProjectForm(request.POST, resume=resume)
		if form.is_valid():
			form.save()
	pro_html = render_to_string('resumebuilder/partial/pro.html', {'projects': resume.get_projects()})
	return JsonResponse({'html': pro_html})

@login_required
def delete_pro(request, id, pro_id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	pro = get_object_or_404(Project, id=pro_id, resume=resume)
	pro.delete()
	pro_html = render_to_string('resumebuilder/partial/pro.html', {'projects': resume.get_projects()})
	return JsonResponse({'html': pro_html})

@login_required
def create_soc(request, id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	if request.method == 'POST':
		form = SocialForm(request.POST, resume=resume)
		if form.is_valid():
			form.save()
	soc_html = render_to_string('resumebuilder/partial/soc.html', {'socials': resume.get_socials()})
	return JsonResponse({'html': soc_html})

@login_required
def delete_soc(request, id, soc_id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	soc = get_object_or_404(Social, id=soc_id, resume=resume)
	soc.delete()
	soc_html = render_to_string('resumebuilder/partial/soc.html', {'socials': resume.get_socials()})
	return JsonResponse({'html': soc_html})

@login_required
def create_lang(request, id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	if request.method == 'POST':
		form = LanguageForm(request.POST, resume=resume)
		if form.is_valid():
			form.save()
	lang_html = render_to_string('resumebuilder/partial/lang.html', {'languages': resume.get_languages()})
	return JsonResponse({'html': lang_html})

@login_required
def delete_lang(request, id, lang_id):
	resume = get_object_or_404(Resume, id=id, user=request.user)
	lang = get_object_or_404(Language, id=lang_id, resume=resume)
	lang.delete()
	lang_html = render_to_string('resumebuilder/partial/lang.html', {'languages': resume.get_languages()})
	return JsonResponse({'html': lang_html})