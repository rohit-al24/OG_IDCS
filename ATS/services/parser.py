
import io
import pdfplumber
import docx
import re
from .analyzer import call_ai_api

def extract_text(file):
	name = file.name.lower()
	if name.endswith('.pdf'):
		with pdfplumber.open(file) as pdf:
			text = ''
			for page in pdf.pages:
				text += page.extract_text() or ''
		return text
	elif name.endswith('.docx'):
		doc = docx.Document(file)
		return '\n'.join([p.text for p in doc.paragraphs])
	elif name.endswith('.txt'):
		return file.read().decode('utf-8')
	else:
		return ''


# Modular AI line analysis

# Modular AI section analysis



def ai_analyze_section(section_name, section_text, jd_text=None):
	"""
	Sends the full section text and full JD to the AI for analysis.
	The AI should return JSON: {"section_score": int, "lines": [{"original": str, "suggestion": str, "reason": str}]}
	Only lines that are not proper or not relevant to the JD should be returned in the 'lines' list.
	"""
	if not section_text.strip():
		return None
	prompt = (
		f"You are an expert resume reviewer and ATS analyzer. "
		f"Here is the job description (JD):\n{jd_text}\n" if jd_text else ""
	)
	prompt += (
		f"Here is a section from a student's resume (section: {section_name}):\n{section_text}\n"
		f"Analyze the section as a whole and each line. "
		f"For each line, if it is not proper (e.g., grammar, clarity, or not relevant to the JD), return it in a list with a suggestion to improve it. "
		f"If the line is fine and relevant, do not include it in the list. "
		f"Give an overall section score (0-100) based on how well the section matches the JD. "
		f"Reply ONLY with JSON: {{'section_score': int, 'lines': [{{'original': str, 'suggestion': str, 'reason': str}}]}}."
	)
	try:
		ai_response = call_ai_api(prompt)
		print(f"[AI DEBUG] AI response for section '{section_name}': {ai_response[:120]}")
		import json
		json_start = ai_response.find('{')
		json_end = ai_response.rfind('}') + 1
		if json_start != -1 and json_end != -1:
			ai_json = ai_response[json_start:json_end]
			data = json.loads(ai_json)
			return {
				"section_score": int(data.get("section_score", 0)),
				"lines": data.get("lines", [])
			}
		else:
			return {"section_score": 0, "lines": []}
	except Exception as e:
		print(f"[AI DEBUG] AI error for section '{section_name}': {e}")
		return {"section_score": 0, "lines": []}


def split_resume_sections(text):
	# Simple heuristic: split by common section headers
	section_headers = [
		"personal info", "personal information", "contact", "education", "academic", "experience", "work", "projects", "skills", "certifications", "achievements", "summary", "objective"
	]
	lines = text.splitlines()
	sections = {}
	current_section = "Other"
	buffer = []
	for line in lines:
		l = line.strip().lower()
		found = False
		for header in section_headers:
			if l.startswith(header):
				# Save previous section
				if buffer:
					sections[current_section] = '\n'.join(buffer).strip()
					buffer = []
				current_section = header.title()
				found = True
				break
		if not found:
			buffer.append(line)
	if buffer:
		sections[current_section] = '\n'.join(buffer).strip()
	return sections



def analyze_resume(text, jd_text=None):
	"""
	Sends the full resume and JD to the AI. Expects a list of flagged lines with section, reason, and suggestion, and an overall score.
	"""
	prompt = (
		f"You are an expert resume reviewer and ATS analyzer.\n"
		f"Here is the job description (JD):\n{jd_text}\n\n"
		f"Here is the full resume:\n{text}\n\n"
		f"Analyze the resume as a whole. For each line, if it is not relevant to the JD or needs improvement, return it in a list with its section, a reason, and a suggestion.\n"
		f"If the line is fine and relevant, do not include it in the list.\n"
		f"Be concise: limit each suggestion to 1-2 sentences. Limit the number of flagged lines to the 5 most important per chunk.\n"
		f"Give an overall resume score (0-100) based on how well the resume matches the JD.\n"
		f"Reply ONLY with JSON: {{'overall_score': int, 'flagged_lines': [{{'section': str, 'original': str, 'reason': str, 'suggestion': str}}]}}."
	)
	import json
	try:
		ai_response = call_ai_api(prompt)
		print(f"[AI DEBUG] AI response for full resume: {ai_response[:120]}")
		json_start = ai_response.find('{')
		json_end = ai_response.rfind('}') + 1
		if json_start != -1 and json_end != -1:
			ai_json = ai_response[json_start:json_end]
			import re
			# Fix single quotes to double quotes for JSON
			ai_json_fixed = re.sub(r"'", '"', ai_json)
			try:
				data = json.loads(ai_json_fixed)
				return {
					"overall": {"score": int(data.get("overall_score", 0))},
					"flagged_lines": data.get("flagged_lines", [])
				}
			except json.JSONDecodeError as e:
				# Robust partial recovery: only add flagged_lines with all required fields, fill missing with empty string
				flagged_lines = []
				score = 0
				try:
					# Extract overall_score manually
					score_match = re.search(r'"overall_score"\s*:\s*(\d+)', ai_json_fixed)
					if score_match:
						score = int(score_match.group(1))
					# Extract flagged_lines array up to last complete or partial object
					flagged_start = ai_json_fixed.find('"flagged_lines"')
					arr_start = ai_json_fixed.find('[', flagged_start)
					arr_str = ai_json_fixed[arr_start:]
					# Find all possible objects, even broken ones
					obj_matches = re.findall(r'\{[^\{\}]*\}', arr_str)
					for obj_str in obj_matches:
						try:
							obj = json.loads(obj_str)
							# Ensure all required fields are present
							for key in ["section", "original", "reason", "suggestion"]:
								if key not in obj:
									obj[key] = ""
							flagged_lines.append(obj)
						except Exception:
							# Try to fix broken objects by trimming at last complete key-value
							last_comma = obj_str.rfind(',')
							if last_comma > 0:
								try:
									fixed_obj = obj_str[:last_comma] + '}'
									obj = json.loads(fixed_obj)
									for key in ["section", "original", "reason", "suggestion"]:
										if key not in obj:
											obj[key] = ""
									flagged_lines.append(obj)
								except Exception:
									continue
							continue
					# Do NOT try to parse a final partial object if it is too broken
				except Exception as e2:
					print(f"[AI DEBUG] Partial JSON extraction failed: {e2}\nRaw AI: {ai_response}")
				print(f"[AI DEBUG] JSON recovery failed: {e}\nRaw AI: {ai_response}")
				return {"overall": {"score": score}, "flagged_lines": flagged_lines, "error": "AI JSON malformed (partial results shown)"}
		else:
			print(f"[AI DEBUG] No JSON found in AI response. Raw: {ai_response}")
			return {"overall": {"score": 0}, "flagged_lines": [], "error": "No JSON in AI response"}
	except Exception as e:
		print(f"[AI DEBUG] AI error for full resume: {e}")
		return {"overall": {"score": 0}, "flagged_lines": [], "error": str(e)}
