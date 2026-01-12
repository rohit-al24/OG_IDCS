
import os
import requests
import re
import json
import dotenv

PERPLEXITY_API_KEY = os.environ.get('PERPLEXITY_API_KEY')
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

def generate_course_plan(data, start=None, end=None):
	"""
	Calls OpenAI API to generate a structured course/career plan.
	For staff, generates only the requested range of periods.
	For students, generates only the requested range of steps.
	Returns a dict: { 'Period 1': {...}, ... } or { 'Step 1': {...}, ... }
	"""

	role = data.get('role')
	if role == 'Student':
		branch = data.get('branch')
		year = data.get('year')
		degree = data.get('degree')
		semester = int(data.get('semester'))
		skills = data.get('skills')
		career_goal = data.get('career_goal')
		st = int(start) if start is not None else 1
		en = int(end) if end is not None else 10
		system_prompt = (
			f"Generate a career roadmap for a {year} year {degree} student in {branch} branch, currently in semester {semester}, with skills: {skills}, who wants to become {career_goal}. "
			f"For semester {semester} ONLY, break down the steps/goals, internships, projects, and job insights needed to achieve the career goal. "
			f"Provide a section for 'Semester {semester}' with steps: for each step, provide Topic, Hints, and Resources. "
			f"Return ONLY valid JSON (no markdown, no extra text, no explanation). "
			f"Format output as JSON: {{'Semester {semester}': {{'Step 1': {{'Topic': ..., 'Hints': ..., 'Resources': ...}}, ...}}}}."
		)
	else:
		branch = data.get('branch')
		subject = data.get('subject')
		syllabus = data.get('syllabus')
		total_periods = int(data.get('total_periods'))
		duration = data.get('duration')
		sp = int(start) if start is not None else 1
		ep = int(end) if end is not None else min(10, total_periods)
		system_prompt = (
			f"Generate a course teaching plan for branch {branch}, subject {subject}, covering {syllabus}, "
			f"split into exactly {ep-sp+1} periods (Period {sp} to Period {ep}), each lasting {duration} minutes. "
			f"For each period, provide: Topic, Hints, and Resources. "
			f"Return ONLY valid JSON (no markdown, no extra text, no explanation). "
			f"Format output as JSON: {{'Period {sp}': {{'Topic': ..., 'Hints': ..., 'Resources': ...}}, ..., 'Period {ep}': {{...}}}}."
		)

	try:
		headers = {
			"Authorization": f"Bearer {PERPLEXITY_API_KEY}",
			"Content-Type": "application/json"
		}
		payload = {
			"model": "sonar-pro",
			"messages": [
				{"role": "user", "content": system_prompt}
			],
			"max_tokens": 1200,
			"temperature": 0.7
		}
		resp = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=60)
		try:
			resp.raise_for_status()
		except requests.exceptions.HTTPError as http_err:
			print("Perplexity API HTTP error:", http_err)
			print("Response content:", resp.text)
			return None
		result = resp.json()
		print("Perplexity API result:", result)
		ai_text = result["choices"][0]["message"]["content"]
		print("Perplexity API ai_text:", ai_text)
		plan = extract_json_from_text(ai_text)
		return plan
	except Exception as e:
		print("Perplexity API error:", e)
		return None

def extract_json_from_text(text):
	"""Extracts and parses JSON object from AI text."""
	try:
		# Try direct JSON parse
		return json.loads(text)
	except Exception:
		# Try to extract JSON substring
		match = re.search(r'({[\s\S]+})', text)
		if match:
			try:
				return json.loads(match.group(1))
			except Exception:
				return None
		return None
