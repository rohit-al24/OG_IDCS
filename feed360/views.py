
from urllib.parse import unquote
from django.db import models

def hod_view_comments_all_custom(request, custom_staff_name, form_id):
	# Show all feedback comments for this custom staff name (across all forms/questions)
	custom_staff_name = unquote(custom_staff_name)
	from .models import FeedbackForm, FeedbackQuestion, FeedbackResponse, Staff
	# Only show comments for the given form_id and custom_staff_name
	form_ids = list(FeedbackForm.objects.filter(staff_name_other=custom_staff_name, id=form_id).values_list('id', flat=True))
	q_ids = list(FeedbackQuestion.objects.filter(staff_name_other=custom_staff_name, form_id=form_id).values_list('id', flat=True))
	responses = FeedbackResponse.objects.filter((models.Q(form_id__in=form_ids) | models.Q(question_id__in=q_ids)), staff__isnull=True)
	comments = []
	for resp in responses:
		if resp.comment:
			comments.append({
				'form_title': resp.form.title,
				'question_text': resp.question.text,
				'comment': resp.comment,
				'student': getattr(resp.student, 'name', str(resp.student)),
				'submitted_at': resp.submitted_at,
			})
	comments = sorted(comments, key=lambda x: x['submitted_at'], reverse=True)
	# Add duser for sidebar context
	try:
		duser = Staff.objects.get(user=request.user)
	except Exception:
		duser = None
	return render(request, 'feed360/hod_view_comments_custom.html', {
		'custom_staff_name': custom_staff_name,
		'comments': comments,
		'duser': duser,
	})
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

# HOD deactivate feedback form
@login_required
@require_POST
def hod_deactivate_form(request, form_id):
	user = request.user
	staff = getattr(user, 'staff', None)
	if not staff or staff.position != 0:
		messages.error(request, "Permission denied. HODs only.")
		return redirect('feed360_hod_list_forms')
	form = get_object_or_404(FeedbackForm, pk=form_id, department=staff.department.name)
	if not form.active:
		messages.info(request, "Form is already inactive.")
	else:
		form.active = False
		form.save()
		messages.success(request, f"Feedback form '{form.title}' deactivated.")
	return redirect('feed360_hod_list_forms')
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from core.models import Staff
from django.db import transaction
from django.contrib import messages
from .models import FeedbackAggregate, FeedbackQuestion, FeedbackResponse, Subject, Staff, Student, FeedbackForm
from .forms import FeedbackFormCreateForm, FeedbackQuestionFormSet
from .services import analyzer

@login_required
def hod_view_comments_all(request, staff_id, form_id):
	# Permission: Only HODs
	user = request.user
	staff = getattr(user, 'staff', None)
	if not staff or staff.position != 0:
		messages.error(request, "Permission denied. HODs only.")
		return redirect('feed360_index')
	try:
		form_id_int = int(form_id)
	except (ValueError, TypeError):
		messages.error(request, "Invalid form ID.")
		return redirect('feed360_hod_staff_feedback_results')
	from .models import Staff, FeedbackForm, FeedbackQuestion, FeedbackResponse, Student
	staff_obj = Staff.objects.get(id=staff_id)
	form = FeedbackForm.objects.get(id=form_id_int)
	# Get all questions for this form
	questions = FeedbackQuestion.objects.filter(form=form)
	# Get all students in the form's department, year, section
	students = Student.objects.filter(
		department__name=form.department,
		year=form.year,
		section=form.section
	)
	questions_data = []
	for question in questions:
		responses = FeedbackResponse.objects.filter(form=form, question=question, staff=staff_obj)
		resp_map = {r.student_id: r for r in responses}
		student_feedback = []
		for student in students:
			resp = resp_map.get(student.id)
			sentiment = None
			if resp and resp.comment:
				# Use stored sentiment_label if available, else analyze
				sentiment = resp.sentiment_label or analyzer.analyze_text_with_perplexity(resp.comment).get('sentiment_label', 'Neutral')
			student_feedback.append({
				'student_name': student.user.get_full_name() if hasattr(student, 'user') else str(student),
				'rating': resp.rating if resp else None,
				'comment': resp.comment if resp else None,
				'sentiment': sentiment if resp and resp.comment else None,
			})
		questions_data.append({
			'text': question.text,
			'student_feedback': student_feedback,
		})
	back_url = reverse('feed360_hod_staff_feedback_results') + f'?staff_id={staff_id}'
	# Fetch duser (Staff) for sidebar context
	duser = Staff.objects.get(user=request.user)
	return render(request, 'feed360/hod_view_comments_all.html', {
		'questions': questions_data,
		'back_url': back_url,
		'duser': duser,
	})
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from .models import FeedbackAggregate, FeedbackQuestion, FeedbackResponse, Subject, Staff, Student, FeedbackForm
from .forms import FeedbackFormCreateForm, FeedbackQuestionFormSet
from .services import analyzer
@login_required
def hod_view_comments(request, staff_id, form_id, question_id):
	# Permission: Only HODs
	user = request.user
	staff = getattr(user, 'staff', None)
	if not staff or staff.position != 0:
		messages.error(request, "Permission denied. HODs only.")
		return redirect('feed360_index')
	# Defensive: Ensure form_id and question_id are integers and not department names
	try:
		form_id_int = int(form_id)
		question_id_int = int(question_id)
	except (ValueError, TypeError):
		messages.error(request, "Invalid form or question ID.")
		return redirect('feed360_hod_staff_feedback_results')
	# Extra check: IDs should not be suspiciously large or small, and not strings like department names
	if not (form_id_int > 0 and question_id_int > 0):
		messages.error(request, "Invalid form or question ID.")
		return redirect('feed360_hod_staff_feedback_results')
	# Get staff, form, question
	from .models import Staff, FeedbackForm, FeedbackQuestion, FeedbackResponse, Student
	staff_obj = Staff.objects.get(id=staff_id)
	form = FeedbackForm.objects.get(id=form_id_int)
	question = get_object_or_404(FeedbackQuestion, id=question_id_int, form=form)
	# The line below causes a ValueError because form.department is a string, 
	# but the Student.department field is a ForeignKey. 
	# Fix this Django query to filter by the department's name instead of its ID.
	students = Student.objects.filter(
		department__name=form.department,
		year=form.year,
		section=form.section
	)
	# Build feedback map: student_id -> response
	responses = FeedbackResponse.objects.filter(form=form, question=question, staff=staff_obj)
	resp_map = {r.student_id: r for r in responses}
	student_feedback = []
	for student in students:
		resp = resp_map.get(student.id)
		student_feedback.append({
			'student_name': student.user.get_full_name() if hasattr(student, 'user') else str(student),
			'rating': resp.rating if resp else None,
			'comment': resp.comment if resp else None,
		})
	back_url = reverse('feed360_hod_staff_feedback_results') + f'?staff_id={staff_id}'
	duser = Staff.objects.get(user=request.user)
	return render(request, 'feed360/hod_view_comments.html', {
		'student_feedback': student_feedback,
		'back_url': back_url,
		'duser': duser,
	})
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from .models import FeedbackAggregate, FeedbackQuestion, FeedbackResponse, Subject, Staff, Student, FeedbackForm
from .forms import FeedbackFormCreateForm, FeedbackQuestionFormSet
from .services import analyzer

@login_required
def staff_my_results(request):
	user = request.user
	staff = getattr(user, 'staff', None)
	if not staff:
		messages.error(request, "Permission denied. Staff only.")
		return redirect('feed360_index')
	# Get all aggregates for this staff
	aggregates = FeedbackAggregate.objects.filter(staff_id=staff.id).order_by('-last_computed')
	print(f"[DEBUG] staff_my_results: staff_id={staff.id}, found {aggregates.count()} aggregates")
	for agg in aggregates:
		print(f"[DEBUG] Aggregate: form_id={agg.form_id}, staff_id={agg.staff_id}, subject_id={agg.subject_id}, avg_rating={agg.avg_rating}, avg_star_rating={agg.avg_star_rating}, avg_sentiment_score={agg.avg_sentiment_score}")
	# Prepare data for trend, word cloud, aspect breakdown
	trend = []
	aspect_labels = set()
	word_freq = {}
	import re
	from collections import Counter
	prev_score = None
	from .models import Staff
	for agg in aggregates:
		# Trend: compare overall_score to previous
		overall_score = None
		if agg.avg_star_rating is not None and agg.avg_sentiment_score is not None:
			overall_score = float(agg.avg_star_rating) * 0.7 + float(agg.avg_sentiment_score) * 0.3
		# Anomaly detection: flag if drop >20% from previous
		anomaly = False
		if prev_score is not None and overall_score is not None:
			if prev_score > 0 and (prev_score - overall_score) / prev_score > 0.2:
				anomaly = True
		# Benchmarking: department average for this form
		dept_avg = None
		if agg.form_id and staff and staff.department:
			dept_staff = Staff.objects.filter(department=staff.department)
			dept_aggregates = FeedbackAggregate.objects.filter(form_id=agg.form_id, staff__in=dept_staff)
			dept_scores = []
			for da in dept_aggregates:
				if da.avg_star_rating is not None and da.avg_sentiment_score is not None:
					score = float(da.avg_star_rating) * 0.7 + float(da.avg_sentiment_score) * 0.3
					dept_scores.append(score)
			if dept_scores:
				dept_avg = round(sum(dept_scores) / len(dept_scores), 2)
		trend.append({
			'form_id': agg.form_id,
			'overall_score': overall_score,
			'anomaly': anomaly,
			'department_average': dept_avg,
		})
		prev_score = overall_score if overall_score is not None else prev_score
		# Aspect breakdown
		if agg.aspect_scores:
			aspect_labels.update(agg.aspect_scores.keys())
		# Word frequency (from comments, if available)
		# (Assume comments are not stored in aggregate, so skip unless you want to aggregate from FeedbackResponse)
	aspect_labels = sorted(list(aspect_labels))
	# Prepare aspect data for chart
	aspect_data = {label: [] for label in aspect_labels}
	for agg in aggregates:
		for label in aspect_labels:
			aspect_data[label].append(agg.aspect_scores.get(label, 0.0) if agg.aspect_scores else 0.0)
	# Sentiment distribution for pie chart
	sentiment_dist = Counter()
	for agg in aggregates:
		if agg.sentiment_distribution:
			sentiment_dist.update(agg.sentiment_distribution)
	# Pass all data to template
	import json
	return render(request, 'feed360/staff_my_results.html', {
		'aggregates': aggregates,
		'trend': trend,
		'aspect_labels': aspect_labels,
		'aspect_data': aspect_data,
		'sentiment_dist': dict(sentiment_dist),
		'trend_json': json.dumps(trend),
		'aspect_labels_json': json.dumps(aspect_labels),
		'aspect_data_json': json.dumps(aspect_data),
		'sentiment_dist_json': json.dumps(dict(sentiment_dist)),
		# 'word_freq': word_freq, # Uncomment if you aggregate words
	})

from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from .models import FeedbackAggregate, FeedbackQuestion, FeedbackResponse, Subject, Staff, Student, FeedbackForm
from .forms import FeedbackFormCreateForm, FeedbackQuestionFormSet
from .services import analyzer

@login_required
def results_for_staff(request, staff_id):
	# Get staff object first
	from core.helpers import set_config
	context = set_config(request)
	try:
		staff = Staff.objects.get(pk=staff_id)
	except Staff.DoesNotExist:
		messages.error(request, "Staff not found.")
		return redirect('feed360_index')
	# Permission check
	user = request.user
	user_staff = getattr(user, 'staff', None)
	if not user_staff:
		messages.error(request, "Permission denied. Staff only.")
		return redirect('feed360_index')
	is_hod = getattr(user_staff, 'position', None) == 0
	if not is_hod and user_staff != staff:
		messages.error(request, "Permission denied.")
		return redirect('feed360_index')
	# Group responses by form and then by question
	from collections import defaultdict, Counter
	responses = FeedbackResponse.objects.filter(staff=staff)
	form_map = defaultdict(list)
	for resp in responses:
		form_map[resp.form_id].append(resp)
	results = []
	for form_id, resps in form_map.items():
		if not resps:
			continue
		form_title = resps[0].form.title
		# Group by question
		question_map = defaultdict(list)
		for resp in resps:
			question_map[resp.question.text].append(resp)
		question_results = []
		for q_text, q_resps in question_map.items():
			ratings = [r.rating for r in q_resps if r.rating is not None]
			avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else '-'
			sentiments = []
			confidences = []
			for r in q_resps:
				# Sentiment analysis (TextBlob only, no AI)
				sent_result = analyzer.analyze_text_with_perplexity(r.comment) if r.comment else {'sentiment_label': 'Neutral', 'sentiment_score': 0.0}
				sentiments.append(sent_result.get('sentiment_label', 'Neutral'))
				confidences.append(sent_result.get('sentiment_score', 0.0))
			label_counter = Counter(sentiments)
			majority = label_counter.most_common(1)[0][0] if sentiments else 'Neutral'
			majority_scores = [score for label, score in zip(sentiments, confidences) if label == majority]
			avg_conf = sum(majority_scores) / len(majority_scores) if majority_scores else 0.0
			question_results.append({
				'question_text': q_text,
				'avg_rating': avg_rating,
				'majority_sentiment': majority,
				'majority_confidence': avg_conf,
			})
		# Calculate overall avg rating for the form
		all_ratings = [qr['avg_rating'] for qr in question_results if isinstance(qr['avg_rating'], (int, float))]
		overall_avg_rating = round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else None
		# Majority sentiment for the form
		all_sentiments = [qr['majority_sentiment'] for qr in question_results]
		label_counter = Counter(all_sentiments)
		form_majority = label_counter.most_common(1)[0][0] if all_sentiments else 'Neutral'
		form_majority_scores = [qr['majority_confidence'] for qr in question_results if qr['majority_sentiment'] == form_majority]
		form_majority_conf = sum(form_majority_scores) / len(form_majority_scores) if form_majority_scores else 0.0
		results.append({
			'form_title': form_title,
			'questions': question_results,
			'overall_avg_rating': overall_avg_rating,
			'majority_sentiment': form_majority,
			'majority_confidence': form_majority_conf,
		})
	# Use same logic as staff_my_results
	aggregates = FeedbackAggregate.objects.filter(staff_id=staff.id).order_by('-last_computed')
	trend = []
	aspect_labels = set()
	word_freq = {}
	import re
	from collections import Counter
	prev_score = None
	for agg in aggregates:
		overall_score = None
		if agg.avg_star_rating is not None and agg.avg_sentiment_score is not None:
			overall_score = float(agg.avg_star_rating) * 0.7 + float(agg.avg_sentiment_score) * 0.3
		anomaly = False
		if prev_score is not None and overall_score is not None:
			if prev_score > 0 and (prev_score - overall_score) / prev_score > 0.2:
				anomaly = True
		# Benchmarking: department average for this form
		dept_avg = None
		if agg.form_id and staff and staff.department:
			dept_staff = Staff.objects.filter(department=staff.department)
			dept_aggregates = FeedbackAggregate.objects.filter(form_id=agg.form_id, staff__in=dept_staff)
			dept_scores = []
			for da in dept_aggregates:
				if da.avg_star_rating is not None and da.avg_sentiment_score is not None:
					score = float(da.avg_star_rating) * 0.7 + float(da.avg_sentiment_score) * 0.3
					dept_scores.append(score)
			if dept_scores:
				dept_avg = round(sum(dept_scores) / len(dept_scores), 2)
		trend.append({
			'form_id': agg.form_id,
			'overall_score': overall_score,
			'anomaly': anomaly,
			'department_average': dept_avg,
		})
		prev_score = overall_score if overall_score is not None else prev_score
		if agg.aspect_scores:
			aspect_labels.update(agg.aspect_scores.keys())
	aspect_labels = sorted(list(aspect_labels))
	aspect_data = {label: [] for label in aspect_labels}
	for agg in aggregates:
		for label in aspect_labels:
			aspect_data[label].append(agg.aspect_scores.get(label, 0.0) if agg.aspect_scores else 0.0)
	sentiment_dist = Counter()
	for agg in aggregates:
		if agg.sentiment_distribution:
			sentiment_dist.update(agg.sentiment_distribution)
	import json
	context.update({
		'aggregates': aggregates,
		'trend': trend,
		'aspect_labels': aspect_labels,
		'aspect_data': aspect_data,
		'sentiment_dist': dict(sentiment_dist),
		'trend_json': json.dumps(trend),
		'aspect_labels_json': json.dumps(aspect_labels),
		'aspect_data_json': json.dumps(aspect_data),
		'sentiment_dist_json': json.dumps(dict(sentiment_dist)),
		'results': results,
	})
	return render(request, 'feed360/staff_my_results.html', context)
from django.forms import formset_factory
from .models import FeedbackQuestion, FeedbackResponse, Subject, Staff, Student

@login_required
def list_active_forms(request):
	# List active forms for student's class
	from django.shortcuts import get_object_or_404
	student = None
	# If user.student is a RelatedManager, use .first(); else use get_object_or_404
	if hasattr(request.user, 'student') and hasattr(request.user.student, 'all'):
		student = request.user.student.first()
	else:
		try:
			student = get_object_or_404(Student, user=request.user)
		except Exception:
			student = None
	if not student:
		messages.error(request, "Student profile not found. Please contact admin.")
		return redirect('dash')
	dept_name = None
	if student.department and hasattr(student.department, 'name'):
		dept_name = student.department.name
	# Debug: print filter values and count
	import logging
	logger = logging.getLogger('django')
	logger.warning(f"Student portal filter: department={dept_name}, year={student.year}, section={student.section}")
	forms = FeedbackForm.objects.filter(active=True, department=dept_name, year=student.year, section=student.section)
	logger.warning(f"Matching forms count: {forms.count()}")
	# Print all FeedbackForm department values for debugging
	all_forms = FeedbackForm.objects.all()
	logger.warning(f"All FeedbackForm departments: {[f'department={f.department}, year={f.year}, section={f.section}' for f in all_forms]}")
	# Add duser for correct profile/header context
	from core.helpers import set_config
	context = set_config(request)
	context['forms'] = forms
	return render(request, 'feed360/student_active_forms.html', context)

@login_required
def fill_feedback_form(request, form_id):
	# Student fills feedback per subject/staff
	from core.models import Student
	from core.helpers import set_config
	try:
		# If user.student is a RelatedManager, use .first(); else get the instance
		if hasattr(request.user, 'student') and hasattr(request.user.student, 'all'):
			student = request.user.student.first()
		else:
			student = Student.objects.get(user=request.user)
	except Exception:
		messages.error(request, "Student profile not found.")
		return redirect('dash')
	feedback_form = FeedbackForm.objects.get(pk=form_id, active=True)
	questions = FeedbackQuestion.objects.filter(form=feedback_form)
	# Use staff_name and staff_name_other for feedback linking
	# If staff_name is '__other__', use staff_name_other
	staff_display_name = feedback_form.staff_name_other if feedback_form.staff_name == '__other__' else feedback_form.staff_name
	# For backward compatibility, if not set, fallback to subject logic
	use_staff_name_linking = bool(staff_display_name)
	# prepare template context including duser/profile
	context = set_config(request)

	if request.method == 'POST':
		responses = []
		affected_staff = set()
		for q in questions:
			# Only one staff per form (by design)
			staff_name = q.staff_name_other if q.staff_name == '__other__' else q.staff_name
			star_key = f'star_{q.id}_staff'
			comment_key = f'comment_{q.id}_staff'
			rating = request.POST.get(star_key)
			comment = request.POST.get(comment_key)
			if q.answer_type in ['stars', 'both'] and not rating:
				messages.error(request, f"Rating required for question '{q.text}' and staff '{staff_name}'.")
				context.update({
					'form': feedback_form,
					'questions': questions,
					'staff_display_name': staff_display_name,
				})
				return render(request, 'feed360/student_fill_form.html', context)
			# Analyze sentiment if comment exists
			sentiment_result = None
			if comment:
				sentiment_result = analyzer.analyze_text_with_perplexity(comment)
			# For now, staff FK is not set for custom names; can be null or a dummy staff
			FeedbackResponse.objects.create(
				form=feedback_form,
				question=q,
				student=student,
				staff=None,  # Not linking to Staff FK for custom names
				rating=rating if rating else None,
				comment=comment if comment else None,
			)
		# Trigger aggregation for affected staff and this form
		for staff in affected_staff:
			responses = FeedbackResponse.objects.filter(form=feedback_form, staff=staff)
			# Aggregate all questions for this (form, staff, subject)
			from collections import Counter, defaultdict
			subject = None
			if responses.exists():
				subject = responses.first().question.subject
			ratings = []
			sentiment_labels = []
			sentiment_scores = []
			emotion_labels = []
			aspect_scores_list = []
			for resp in responses:
				if resp.rating:
					ratings.append(resp.rating)
				if resp.comment:
					# Sentiment analysis (TextBlob only, no AI)
					sent_result = analyzer.analyze_text_with_perplexity(resp.comment)
					sentiment_labels.append(sent_result.get('sentiment_label', 'Neutral'))
					sentiment_scores.append(sent_result.get('sentiment_score', 0.0))
					emotion_labels.append(sent_result.get('emotion_label', ''))
					aspect_scores_list.append(sent_result.get('aspect_scores', {}))
			avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
			avg_star_rating = avg_rating
			avg_sentiment_score = round(sum(sentiment_scores) / len(sentiment_scores), 2) if sentiment_scores else 0.0
			sentiment_dist = dict(Counter(sentiment_labels))
			aspect_totals = defaultdict(float)
			aspect_counts = defaultdict(int)
			for aspect_dict in aspect_scores_list:
				for aspect, score in aspect_dict.items():
					aspect_totals[aspect] += score
					aspect_counts[aspect] += 1
			aspect_scores = {a: round(aspect_totals[a]/aspect_counts[a], 2) if aspect_counts[a] else 0.0 for a in aspect_totals}
			print(f"[DEBUG] Creating/updating FeedbackAggregate: form_id={feedback_form.id}, staff_id={staff.id}, subject_id={subject.id if subject else None}, avg_rating={avg_rating}, avg_star_rating={avg_star_rating}, avg_sentiment_score={avg_sentiment_score}, sentiment_dist={sentiment_dist}, aspect_scores={aspect_scores}")
			FeedbackAggregate.objects.update_or_create(
				form_id=feedback_form.id,
				staff_id=staff.id,
				subject_id=subject.id if subject else None,
				defaults={
					'avg_rating': avg_rating,
					'avg_star_rating': avg_star_rating,
					'avg_sentiment_score': avg_sentiment_score,
					'sentiment_score': avg_sentiment_score,
					'sentiment_distribution': sentiment_dist,
					'aspect_scores': aspect_scores,
					'last_computed': timezone.now(),
				}
			)
		messages.success(request, "Feedback submitted successfully.")
		return redirect('feed360_index')
	# final render with full context (includes duser)
	context.update({
		'form': feedback_form,
		'questions': questions,
		'staff_display_name': staff_display_name,
	})
	return render(request, 'feed360/student_fill_form.html', context)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from .forms import FeedbackFormCreateForm, FeedbackQuestionFormSet
from .models import FeedbackForm

@login_required
def create_feedback_form(request):
	# Only allow HOD users (core.models.Staff.position == 0)
	user = request.user
	try:
		staff = user.staff
		is_hod = getattr(staff, 'position', None) == 0
	except Exception:
		is_hod = False
	if not is_hod:
		messages.error(request, "You do not have permission to create feedback forms.")
		return redirect('feed360_index')

	if request.method == 'POST':
		form = FeedbackFormCreateForm(request.POST, user=request.user)
		formset = FeedbackQuestionFormSet(request.POST)
		if form.is_valid() and formset.is_valid():
			with transaction.atomic():
				feedback_form = form.save(commit=False)
				feedback_form.created_by = user
				feedback_form.save()
				# Get common fields
				answer_type = form.cleaned_data.get('answer_type')
				subject = form.cleaned_data.get('subject')
				subject_text = form.cleaned_data.get('subject_text')
				staff_name = form.cleaned_data.get('staff_name')
				staff_name_other = form.cleaned_data.get('staff_name_other') if staff_name == '__other__' else ''
				# Save questions with common fields
				questions = formset.save(commit=False)
				for q in questions:
					q.form = feedback_form
					q.answer_type = answer_type
					q.subject = subject
					q.subject_text = subject_text
					q.staff_name = staff_name
					q.staff_name_other = staff_name_other
					q.save()
				formset.save_m2m()
			messages.success(request, "Feedback form created successfully.")
			return redirect('feed360_index')
	else:
		form = FeedbackFormCreateForm(user=request.user)
		formset = FeedbackQuestionFormSet()

	duser = None
	try:
		duser = Staff.objects.get(user=request.user)
	except Exception:
		duser = None
	return render(request, 'feed360/hod_create_form.html', {
		'form': form,
		'formset': formset,
		'duser': duser,
	})

@login_required
def hod_list_forms(request):
	user = request.user
	staff = getattr(user, 'staff', None)
	if not staff or staff.position != 0:
		return redirect('feed360_index')
	dept_name = staff.department.name if staff.department else None
	forms = FeedbackForm.objects.filter(department=dept_name).order_by('-created_at')
	duser = Staff.objects.get(user=request.user)
	return render(request, 'feed360/hod_list_forms.html', {
		'forms': forms,
		'department_name': dept_name,
		'duser': duser,
	})

@login_required
def hod_results_form(request, form_id):
	# --- Staff × Aspect Heatmap Data ---
	# 1. Collect all unique aspect labels
	user = request.user
	staff = getattr(user, 'staff', None)
	if not staff:
		messages.error(request, "Permission denied. Staff only.")
		return redirect('feed360_index')
	if staff.position != 0:
		messages.error(request, "Permission denied. HODs only.")
		return redirect('feed360_index')
	form = FeedbackForm.objects.get(pk=form_id)
	# Get all staff in this department
	dept_staff = Staff.objects.filter(department=staff.department)
	all_aspect_labels = set()
	staff_aspect_scores = []  # List of dicts: {staff: s, aspect_scores: {aspect: score, ...}}
	for s in dept_staff:
		aggregates = FeedbackAggregate.objects.filter(form=form, staff=s)
		aspect_agg = {}
		for agg in aggregates:
			if agg.aspect_scores:
				for aspect, score in agg.aspect_scores.items():
					all_aspect_labels.add(aspect)
					# Average per aspect per staff
					aspect_agg.setdefault(aspect, []).append(float(score))
		# Compute mean for each aspect for this staff
		aspect_means = {a: round(sum(scores)/len(scores), 2) if scores else None for a, scores in aspect_agg.items()}
		staff_aspect_scores.append({'staff': s, 'aspect_means': aspect_means})
	aspect_labels = sorted(list(all_aspect_labels))
	# 2. Build heatmap matrix: rows=staff, cols=aspect, values=score
	heatmap_matrix = []
	staff_names = []
	for entry in staff_aspect_scores:
		staff_names.append(entry['staff'].name)
		row = [entry['aspect_means'].get(a, None) for a in aspect_labels]
		heatmap_matrix.append(row)
	# For each staff, aggregate feedback responses for this form
	staff_results = []
	overview_table = []  # List of dicts: staff, avg_rating, avg_sentiment
	# Aggregate sentiment distribution for department-level pie chart
	from collections import Counter
	dept_sentiment_dist = Counter()
	for s in dept_staff:
		# Use FeedbackAggregate for this form and staff
		aggregates = FeedbackAggregate.objects.filter(form=form, staff=s)
		# Aggregate sentiment distribution for this staff
		for agg in aggregates:
			if agg.sentiment_distribution:
				dept_sentiment_dist.update(agg.sentiment_distribution)
		# For the overview, calculate mean of avg_star_rating and avg_sentiment_score
		avg_rating = None
		avg_sentiment = None
		if aggregates.exists():
			ratings = [float(a.avg_star_rating) for a in aggregates if a.avg_star_rating is not None]
			sentiments = [float(a.avg_sentiment_score) for a in aggregates if a.avg_sentiment_score is not None]
			avg_rating = round(sum(ratings)/len(ratings), 2) if ratings else None
			avg_sentiment = round(sum(sentiments)/len(sentiments), 2) if sentiments else None
		overview_table.append({
			'staff': s,
			'avg_rating': avg_rating,
			'avg_sentiment': avg_sentiment,
		})
		# For detailed per-question table (existing logic)
		responses = FeedbackResponse.objects.filter(form=form, staff=s)
		if not responses.exists():
			continue
		agg_map = {}
		for resp in responses:
			key = (resp.question_id,)
			if key not in agg_map:
				agg_map[key] = {'ratings': [], 'comments': []}
			if resp.rating:
				agg_map[key]['ratings'].append(resp.rating)
			if resp.comment:
				agg_map[key]['comments'].append(resp.comment)
		aggregates_list = []
		for key, data in agg_map.items():
			avg_rating_q = round(sum(data['ratings']) / len(data['ratings']), 2) if data['ratings'] else None
			aggregates_list.append({
				'question_id': key[0],
				'avg_rating': avg_rating_q,
				'comments': data['comments'],
			})
		staff_results.append({'staff': s, 'aggregates': aggregates_list})
	# Prepare sentiment labels and values for Chart.js
	sentiment_labels = list(dept_sentiment_dist.keys())
	sentiment_values = list(dept_sentiment_dist.values())

	# --- Summary generation (no AI, only TextBlob for sentiment) ---
	# Example: "70% of students are satisfied with clarity..."
	total_responses = sum(sentiment_values)
	positive_count = dept_sentiment_dist.get('Positive', 0)
	neutral_count = dept_sentiment_dist.get('Neutral', 0)
	negative_count = dept_sentiment_dist.get('Negative', 0)
	if total_responses > 0:
		pos_pct = round(100 * positive_count / total_responses)
		neu_pct = round(100 * neutral_count / total_responses)
		neg_pct = round(100 * negative_count / total_responses)
	else:
		pos_pct = neu_pct = neg_pct = 0
	# Find top aspect (by average across all staff)
	aspect_summary = ""
	if aspect_labels:
		aspect_avgs = {}
		for i, aspect in enumerate(aspect_labels):
			aspect_scores = [row[i] for row in heatmap_matrix if row[i] is not None]
			if aspect_scores:
				aspect_avgs[aspect] = round(sum(aspect_scores)/len(aspect_scores), 2)
		if aspect_avgs:
			top_aspect = max(aspect_avgs, key=aspect_avgs.get)
			aspect_summary = f" Top aspect: {top_aspect} ({aspect_avgs[top_aspect]}/5)."
	summary = f"{pos_pct}% of students gave positive feedback, {neu_pct}% neutral, {neg_pct}% negative.{aspect_summary}"

	duser = Staff.objects.get(user=request.user)
	return render(request, 'feed360/hod_results_staff.html', {
		'form': form,
		'staff_results': staff_results,
		'overview_table': overview_table,
		'sentiment_labels': sentiment_labels,
		'sentiment_values': sentiment_values,
		'aspect_labels': aspect_labels,
		'staff_names': staff_names,
		'heatmap_matrix': heatmap_matrix,
		'summary': summary,
		'duser': duser,
	})

@login_required
def hod_staff_feedback_results(request):
	user = request.user
	staff = getattr(user, 'staff', None)
	if not staff:
		messages.error(request, "Permission denied. Staff only.")
		return redirect('feed360_index')
	if staff.position != 0:
		messages.error(request, "Permission denied. HODs only.")
		return redirect('feed360_index')
	dept = staff.department
	staff_list = list(Staff.objects.filter(department=dept))
	from .models import FeedbackForm, FeedbackQuestion
	custom_staff_names = set()
	# From FeedbackForm
	for form in FeedbackForm.objects.filter(department=dept.name):
		if form.staff_name == '__other__' and form.staff_name_other:
			custom_staff_names.add(form.staff_name_other)
		elif form.staff_name and form.staff_name != '__other__':
			if not any(s.name == form.staff_name for s in staff_list):
				custom_staff_names.add(form.staff_name)
	# From FeedbackQuestion (for legacy or per-question custom names)
	for q in FeedbackQuestion.objects.filter(form__department=dept.name):
		if q.staff_name == '__other__' and q.staff_name_other:
			custom_staff_names.add(q.staff_name_other)
		elif q.staff_name and q.staff_name != '__other__':
			if not any(s.name == q.staff_name for s in staff_list):
				custom_staff_names.add(q.staff_name)
	# Build staff_dropdown as (value, label) tuples
	staff_dropdown = [(str(s.id), s.name) for s in staff_list] + [(f"custom_{name}", name) for name in sorted(custom_staff_names)]
	selected_staff_id = request.GET.get('staff_id')
	selected_staff = None
	results = []
	is_custom_staff = False
	import json
	from collections import Counter
	from django.db import models
	from .models import FeedbackForm, FeedbackQuestion, FeedbackResponse
	trend_json = '[]'
	aspect_labels_json = '[]'
	aspect_data_json = '{}'
	sentiment_dist_json = '{}'
	responses = []
	if selected_staff_id:
		if str(selected_staff_id).startswith('custom_'):
			is_custom_staff = True
			# Custom staff name (Others)
			custom_name = str(selected_staff_id)[7:]
			form_ids = list(FeedbackForm.objects.filter(staff_name_other=custom_name).values_list('id', flat=True))
			q_ids = list(FeedbackQuestion.objects.filter(staff_name_other=custom_name).values_list('id', flat=True))
			responses = FeedbackResponse.objects.filter(
				(models.Q(form_id__in=form_ids) | models.Q(question_id__in=q_ids)),
				staff__isnull=True
			)
			selected_staff = custom_name
			# Group by form and question
			agg_map = {}
			for resp in responses:
				key = (resp.form_id, resp.question_id)
				if key not in agg_map:
					agg_map[key] = {'ratings': [], 'sentiments': [], 'form_title': resp.form.title, 'question_text': resp.question.text}
				if resp.rating:
					agg_map[key]['ratings'].append(resp.rating)
				if resp.comment:
					sent_result = analyzer.analyze_text_with_perplexity(resp.comment)
					agg_map[key]['sentiments'].append(sent_result)
			sentiment_dist = Counter()
			for (form_id, question_id), data in agg_map.items():
				avg_rating = round(sum(data['ratings']) / len(data['ratings']), 2) if data['ratings'] else None
				sentiment_labels = [s.get('sentiment_label', 'Neutral') for s in data['sentiments']]
				sentiment_scores = [float(s.get('sentiment_score', 0.0)) for s in data['sentiments']]
				if sentiment_labels:
					label_counter = Counter(sentiment_labels)
					majority = label_counter.most_common(1)[0][0]
					majority_scores = [score for label, score in zip(sentiment_labels, sentiment_scores) if label == majority]
					avg_conf = sum(majority_scores) / len(majority_scores) if majority_scores else 0.0
					sentiment_dist.update(sentiment_labels)
				else:
					majority = 'Neutral'
					avg_conf = 0.0
				comments = []
				for resp in responses:
					if resp.form_id == form_id and resp.question_id == question_id and resp.comment:
						comments.append(resp.comment)
				try:
					form_id_int = int(form_id)
				except Exception:
					import logging
					logging.warning(f"Skipping result with invalid form_id: {form_id}")
					continue
				results.append({
					'form_title': data['form_title'],
					'form_id': form_id_int,
					'question_id': question_id,
					'question_text': data['question_text'],
					'avg_rating': avg_rating,
					'sentiment': majority,
					'confidence': avg_conf,
					'comments': comments,
				})
			sentiment_dist_json = json.dumps(dict(sentiment_dist))
			# No trend/aspect/sentiment charts for custom staff
		else:
			try:
				selected_staff = Staff.objects.get(id=selected_staff_id, department=dept)
				responses = FeedbackResponse.objects.filter(staff=selected_staff)
				# Group by form and question
				agg_map = {}
				for resp in responses:
					key = (resp.form_id, resp.question_id)
					if key not in agg_map:
						agg_map[key] = {'ratings': [], 'sentiments': [], 'form_title': resp.form.title, 'question_text': resp.question.text}
					if resp.rating:
						agg_map[key]['ratings'].append(resp.rating)
					if resp.comment:
						sent_result = analyzer.analyze_text_with_perplexity(resp.comment)
						agg_map[key]['sentiments'].append(sent_result)
				for (form_id, question_id), data in agg_map.items():
					avg_rating = round(sum(data['ratings']) / len(data['ratings']), 2) if data['ratings'] else None
					sentiment_labels = [s.get('sentiment_label', 'Neutral') for s in data['sentiments']]
					sentiment_scores = [float(s.get('sentiment_score', 0.0)) for s in data['sentiments']]
					if sentiment_labels:
						label_counter = Counter(sentiment_labels)
						majority = label_counter.most_common(1)[0][0]
						majority_scores = [score for label, score in zip(sentiment_labels, sentiment_scores) if label == majority]
						avg_conf = sum(majority_scores) / len(majority_scores) if majority_scores else 0.0
					else:
						majority = 'Neutral'
						avg_conf = 0.0
					comments = []
					for resp in responses:
						if resp.form_id == form_id and resp.question_id == question_id and resp.comment:
							comments.append(resp.comment)
					try:
						form_id_int = int(form_id)
					except Exception:
						import logging
						logging.warning(f"Skipping result with invalid form_id: {form_id}")
						continue
					results.append({
						'form_title': data['form_title'],
						'form_id': form_id_int,
						'question_id': question_id,
						'question_text': data['question_text'],
						'avg_rating': avg_rating,
						'sentiment': majority,
						'confidence': avg_conf,
						'comments': comments,
					})
				# --- Add staff dashboard chart data ---
				from .models import FeedbackAggregate
				aggregates = FeedbackAggregate.objects.filter(staff_id=selected_staff.id).order_by('-last_computed')
				trend = []
				aspect_labels = set()
				prev_score = None
				for agg in aggregates:
					overall_score = None
					if agg.avg_star_rating is not None and agg.avg_sentiment_score is not None:
						overall_score = float(agg.avg_star_rating) * 0.7 + float(agg.avg_sentiment_score) * 0.3
					anomaly = False
					if prev_score is not None and overall_score is not None:
						if prev_score > 0 and (prev_score - overall_score) / prev_score > 0.2:
							anomaly = True
					dept_avg = None
					if agg.form_id and selected_staff and selected_staff.department:
						dept_staff = Staff.objects.filter(department=selected_staff.department)
						dept_aggregates = FeedbackAggregate.objects.filter(form_id=agg.form_id, staff__in=dept_staff)
						dept_scores = []
						for da in dept_aggregates:
							if da.avg_star_rating is not None and da.avg_sentiment_score is not None:
								score = float(da.avg_star_rating) * 0.7 + float(da.avg_sentiment_score) * 0.3
								dept_scores.append(score)
						if dept_scores:
							dept_avg = round(sum(dept_scores) / len(dept_scores), 2)
					trend.append({
						'form_id': agg.form_id,
						'overall_score': overall_score,
						'anomaly': anomaly,
						'department_average': dept_avg,
					})
					prev_score = overall_score if overall_score is not None else prev_score
					if agg.aspect_scores:
						aspect_labels.update(agg.aspect_scores.keys())
				aspect_labels = sorted(list(aspect_labels))
				aspect_data = {label: [] for label in aspect_labels}
				for agg in aggregates:
					for label in aspect_labels:
						aspect_data[label].append(agg.aspect_scores.get(label, 0.0) if agg.aspect_scores else 0.0)
				sentiment_dist = Counter()
				for agg in aggregates:
					if agg.sentiment_distribution:
						sentiment_dist.update(agg.sentiment_distribution)
				trend_json = json.dumps(trend)
				aspect_labels_json = json.dumps(aspect_labels)
				aspect_data_json = json.dumps(aspect_data)
				sentiment_dist_json = json.dumps(dict(sentiment_dist))
			except Staff.DoesNotExist:
				selected_staff = None
				trend_json = '[]'
				aspect_labels_json = '[]'
				aspect_data_json = '{}'
				sentiment_dist_json = '{}'
	else:
		trend_json = '[]'
		aspect_labels_json = '[]'
		aspect_data_json = '{}'
		sentiment_dist_json = '{}'
	duser = Staff.objects.get(user=request.user)
	return render(request, 'feed360/hod_staff_feedback_results.html', {
		'staff_list': staff_list,
		'staff_dropdown': staff_dropdown,
		'selected_staff': selected_staff,
		'selected_staff_id': selected_staff_id,
		'results': results,
		'trend_json': trend_json,
		'aspect_labels_json': aspect_labels_json,
		'aspect_data_json': aspect_data_json,
		'sentiment_dist_json': sentiment_dist_json,
		'duser': duser,
		'is_custom_staff': is_custom_staff,
	})
