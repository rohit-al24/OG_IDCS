
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from .forms import ResumeUploadForm
from .models import UploadedResume, ResumeAnalysis
from .services.parser import extract_text, analyze_resume
from core.models import Student

# Loading page for resume analysis
@login_required
@ensure_csrf_cookie
def resume_loading(request, resume_id):
    resume = get_object_or_404(UploadedResume, id=resume_id, student__user=request.user)
    # The URL to redirect to after loading (analysis result)
    analysis_url = reverse('ATS:resume_analysis', args=[resume.id])
    return render(request, 'ATS/resume_loading.html', {
        'resume': resume,
        'analysis_url': analysis_url,
    })


@login_required
def ats_dashboard(request):
	user = request.user
	if user.is_staff:
		return render(request, 'ATS/ats_dashboard.html', {'error': 'Only students can access the dashboard.'})

	try:
		student = Student.objects.get(user=user)
	except Student.DoesNotExist:
		return render(request, 'ATS/ats_dashboard.html', {'error': 'Only students can access the dashboard.'})

	resumes = UploadedResume.objects.filter(student=student).order_by('-uploaded_at')
	resume_data = []
	for resume in resumes:
		analysis_obj = ResumeAnalysis.objects.filter(resume=resume).order_by('-created_at').first()
		ats_score = None
		if analysis_obj:
			ats_score = analysis_obj.results.get('overall', {}).get('ats')
		resume_data.append({
			'resume': resume,
			'ats_score': ats_score,
		})

	return render(request, 'ATS/ats_dashboard.html', {
		'resume_data': resume_data,
	})

@login_required
def upload_resume(request):
	user = request.user
	try:
		student = Student.objects.get(user=user)
	except Student.DoesNotExist:
		return render(request, 'ATS/upload_resume.html', {'form': None, 'error': 'Only students can upload resumes.'})

	if request.method == 'POST':
		form = ResumeUploadForm(request.POST, request.FILES)
		if form.is_valid():
			file = form.cleaned_data['file']
			jd = form.cleaned_data['jd']
			text = extract_text(file)
			resume = UploadedResume.objects.create(
				student=student,
				file=file,
				extracted_text=text
			)
			# Store JD in session for later analysis (or save to model if needed)
			request.session['uploaded_jd'] = jd
			return redirect('ATS:resume_preview', resume_id=resume.id)
	else:
		form = ResumeUploadForm()
	return render(request, 'ATS/upload_resume.html', {'form': form})

@login_required
def resume_preview(request, resume_id):
	resume = get_object_or_404(UploadedResume, id=resume_id, student__user=request.user)
	return render(request, 'ATS/resume_preview.html', {'resume': resume})




@login_required
def resume_analysis(request, resume_id):
	resume = get_object_or_404(UploadedResume, id=resume_id, student__user=request.user)
	# Only allow students (not staff)
	if request.user.is_staff:
		return render(request, 'ATS/resume_analysis.html', {'resume': resume, 'error': 'Only students can access analysis.'})

	# Get JD from session (if available)
	jd = request.session.get('uploaded_jd', None)

	# Support chunked re-analysis for cutoff content
	chunk_size = 1000
	# Initialize or get accumulated flagged lines from session

	if 'accumulated_flagged_lines' not in request.session:
		request.session['accumulated_flagged_lines'] = []
	if 'overall_score_fixed' not in request.session:
		request.session['overall_score_fixed'] = None
	accumulated_flagged_lines = request.session['accumulated_flagged_lines']

	if request.method == 'POST' and 'analyze_more' in request.POST:
		last_offset = request.session.get('last_analysis_offset', 0)
		next_offset = last_offset + chunk_size
		resume_text = resume.extracted_text[next_offset:next_offset+chunk_size]
		jd_text = jd
		analysis = analyze_resume(resume_text, jd_text=jd_text)
		request.session['last_analysis_offset'] = next_offset
		new_flagged = analysis.get('flagged_lines', [])
		# Deduplicate flagged lines by (section, original, suggestion)
		seen = set((f["section"], f["original"], f.get("suggestion", "")) for f in accumulated_flagged_lines)
		for f in new_flagged:
			key = (f["section"], f["original"], f.get("suggestion", ""))
			if key not in seen:
				accumulated_flagged_lines.append(f)
				seen.add(key)
		request.session['accumulated_flagged_lines'] = accumulated_flagged_lines
		# Keep the overall score fixed from the first chunk
		overall_score_fixed = request.session.get('overall_score_fixed', None)
		if overall_score_fixed is None:
			overall_score_fixed = analysis.get('overall', {}).get('score', 0)
			request.session['overall_score_fixed'] = overall_score_fixed
		ai_error = analysis.get('error', None)
		return render(request, 'ATS/resume_analysis.html', {
			'resume': resume,
			'overall': {'score': overall_score_fixed},
			'lines_to_improve': accumulated_flagged_lines,
			'resume_text': resume.extracted_text,
			'ai_error': ai_error,
		})
	# Default: show first chunk or cached analysis
	request.session['last_analysis_offset'] = 0
	analysis_obj = ResumeAnalysis.objects.filter(resume=resume).order_by('-created_at').first()
	if analysis_obj:
		analysis = analysis_obj.results
		flagged_lines = analysis.get('flagged_lines', [])
		overall_score_fixed = analysis.get('overall', {}).get('score', 0)
	else:
		analysis = analyze_resume(resume.extracted_text[:chunk_size], jd_text=jd)
		ResumeAnalysis.objects.create(resume=resume, results=analysis)
		flagged_lines = analysis.get('flagged_lines', [])
		overall_score_fixed = analysis.get('overall', {}).get('score', 0)
	request.session['accumulated_flagged_lines'] = flagged_lines
	request.session['overall_score_fixed'] = overall_score_fixed

	ai_error = analysis.get('error', None)

	return render(request, 'ATS/resume_analysis.html', {
		'resume': resume,
		'overall': {'score': overall_score_fixed},
		'lines_to_improve': flagged_lines,
		'resume_text': resume.extracted_text,
		'ai_error': ai_error,
	})
