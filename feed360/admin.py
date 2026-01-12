
from django.contrib import admin
from .models import FeedbackForm, FeedbackQuestion, FeedbackResponse, FeedbackAggregate


# Only register Subject if it's not SemesterSubject (which is already registered in core.admin)
try:
	from .models import Subject
	from core.models import SemesterSubject
	if Subject is not SemesterSubject:
		admin.site.register(Subject)
except ImportError:
	pass

admin.site.register(FeedbackForm)
admin.site.register(FeedbackQuestion)
admin.site.register(FeedbackResponse)
admin.site.register(FeedbackAggregate)
