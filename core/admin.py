from django import forms
from .models import Department
from django.contrib import admin
from django.http import HttpResponse
import csv
from .models import Semester, SemesterSubject, Student
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import Principal
from .models import Section
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student, Staff, OD, LEAVE, GATEPASS, HOD, AHOD, StaffRating, RatingQuestions, IndividualStaffRating, SpotFeedback, BONAFIDE, Semester, SportsOD, SportsODPlayer
from django import forms as djforms
from django.utils.safestring import mark_safe
import datetime
from .models import Notice, Circular

class SemesterSubjectAdminForm(forms.ModelForm):
	class Meta:
		model = SemesterSubject
		fields = '__all__'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		semester = self.instance.semester if self.instance and self.instance.pk else None
		department = semester.department if semester else None
		# If not editing, try to get semester from form data
		if not department and 'semester' in self.data:
			try:
				sem_id = self.data.get('semester')
				if sem_id:
					semester = Semester.objects.get(pk=sem_id)
					department = semester.department
			except Exception:
				pass
		# Show all sections if no department, else filter
		if department:
			section_qs = Section.objects.filter(department=department)
		else:
			section_qs = Section.objects.all()
		self.fields['section1'].queryset = section_qs
		self.fields['section2'].queryset = section_qs
		self.fields['section3'].queryset = section_qs
		self.fields['section1'].help_text = 'Select a semester first to filter sections by department.'
		self.fields['section2'].help_text = 'Select a semester first to filter sections by department.'
		self.fields['section3'].help_text = 'Select a semester first to filter sections by department.'

# Custom admin for SemesterSubject
@admin.register(SemesterSubject)
class SemesterSubjectAdmin(admin.ModelAdmin):
	form = SemesterSubjectAdminForm
	list_display = ("name", "semester", "staff1", "staff2", "staff3", "section1", "section2", "section3")
	search_fields = ("name", "semester__department__name")


class PrincipalAdmin(DefaultUserAdmin):
	def get_queryset(self, request):
		qs = super().get_queryset(request)
		return qs.filter(principal_status=True)

	list_display = DefaultUserAdmin.list_display + ('principal_status',)
	list_filter = DefaultUserAdmin.list_filter
	fieldsets = DefaultUserAdmin.fieldsets + (
		('Principal Status', {'fields': ('principal_status',)}),
	)

admin.site.register(Principal, PrincipalAdmin)


class CustomUserAdmin(DefaultUserAdmin):
	list_display = DefaultUserAdmin.list_display + ('principal_status',)
	list_filter = DefaultUserAdmin.list_filter
	fieldsets = DefaultUserAdmin.fieldsets + (
		('Principal Status', {'fields': ('principal_status',)}),
	)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class StudentAdminForm(forms.ModelForm):
	class Meta:
		model = Student
		fields = '__all__'

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		# Get department and semester from instance or initial data
		department = None
		semester = None
		if self.instance and self.instance.pk:
			department = self.instance.department
			semester = self.instance.semester
		elif 'department' in self.data and 'semester' in self.data:
			try:
				department = self.data.get('department')
				semester = self.data.get('semester')
			except Exception:
				pass
		# Filter elective fields to only show subjects marked as elective
		qs = SemesterSubject.objects.filter(is_elective=True)
		if department and semester:
			qs = qs.filter(semester__department=department, semester__semester=semester)
		self.fields['elective1'].queryset = qs
		self.fields['elective2'].queryset = qs
		self.fields['elective3'].queryset = qs

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
	form = StudentAdminForm
	list_display = ("user", "department", "semester", "elective1", "elective2", "elective3")
	search_fields = ("user__username", "department__name")

try:
	import openpyxl
	from openpyxl.utils import get_column_letter
	has_openpyxl = True
except ImportError:
	has_openpyxl = False

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):

	list_display = ('code', 'name', 'hod', 'ahod')
	search_fields = ('code', 'name')

	def formfield_for_manytomany(self, db_field, request, **kwargs):
		from .models import Staff
		if db_field.name == 'staffs':
			# Only show staff with this department assigned
			if request.resolver_match and request.resolver_match.url_name == 'core_department_add':
				kwargs['queryset'] = Staff.objects.none()
			else:
				# For change view, filter by department
				obj_id = request.resolver_match.kwargs.get('object_id') if request.resolver_match else None
				if obj_id:
					from .models import Department
					try:
						dept = Department.objects.get(pk=obj_id)
						kwargs['queryset'] = Staff.objects.filter(department=dept)
					except Department.DoesNotExist:
						kwargs['queryset'] = Staff.objects.none()
				else:
					kwargs['queryset'] = Staff.objects.none()
		return super().formfield_for_manytomany(db_field, request, **kwargs)




def export_students_csv(modeladmin, request, queryset):
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename=students.csv'
	writer = csv.writer(response)
	fields = ['id', 'user', 'roll', 'name', 'department', 'semester', 'year', 'section', 'address', 'mobile', 'parent_mobile', 'dob', 'age']
	writer.writerow(fields)
	for obj in queryset:
		writer.writerow([
			obj.id,
			obj.user.username if obj.user else '',
			obj.roll,
			obj.name,
			obj.department,
			obj.semester,
			obj.year,
			obj.section,
			obj.address,
			obj.mobile,
			obj.parent_mobile,
			obj.dob,
			obj.age
		])
	return response
export_students_csv.short_description = "Export Selected Students as CSV"

def export_students_excel(modeladmin, request, queryset):
	if not has_openpyxl:
		return HttpResponse("openpyxl is not installed.")
	from openpyxl import Workbook
	response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
	response['Content-Disposition'] = 'attachment; filename=students.xlsx'
	wb = Workbook()
	ws = wb.active
	fields = ['id', 'user', 'roll', 'name', 'department', 'semester', 'year', 'section', 'address', 'mobile', 'parent_mobile', 'dob', 'age']
	ws.append(fields)
	for obj in queryset:
		ws.append([
			obj.id,
			obj.user.username if obj.user else '',
			obj.roll,
			obj.name,
			obj.department,
			obj.semester,
			obj.year,
			obj.section,
			obj.address,
			obj.mobile,
			obj.parent_mobile,
			obj.dob,
			obj.age
		])
	wb.save(response)
	return response
export_students_excel.short_description = "Export Selected Students as Excel"

class StudentImportForm(forms.Form):
	csv_file = forms.FileField(label="Select CSV file")


class StudentAdmin(admin.ModelAdmin):
	form = StudentAdminForm
	actions = [export_students_csv, export_students_excel]
	change_list_template = "admin/core/student_changelist.html"
	ordering = ['id']  # Default ordering (ascending by id)
	list_display = ('id', 'user', 'roll', 'name', 'department', 'semester', 'year', 'section', 'mobile', 'batch_display', 'academic_year_display')
	list_filter = ('department', 'semester', 'year', 'section', 'batch', 'academic_year')
	search_fields = ('name', 'roll', 'user__username', 'department', 'mobile', 'parent_mobile', 'batch', 'academic_year')

	def batch_display(self, obj):
		return obj.batch_range
	batch_display.short_description = 'Batch (4yr)'

	def academic_year_display(self, obj):
		return obj.academic_year_range
	academic_year_display.short_description = 'Academic Year (1yr)'

	def get_urls(self):
		urls = super().get_urls()
		custom_urls = [
			path('import-students/', self.admin_site.admin_view(self.import_students), name='import-students'),
		]
		return custom_urls + urls

	def import_students(self, request):
		if request.method == "POST":
			form = StudentImportForm(request.POST, request.FILES)
			if form.is_valid():
				csv_file = form.cleaned_data['csv_file']
				import csv
				import io
				from datetime import datetime
				decoded_file = csv_file.read().decode('utf-8')
				reader = csv.DictReader(io.StringIO(decoded_file))
				created = 0
				updated = 0
				from django.contrib.auth.models import User
				for row in reader:
					username = row.get('user')

					if not username or not username.isdigit():
						continue
					user, created_user = User.objects.get_or_create(username=username)
					if created_user:
						user.set_password('123')
						user.save()

					student, created_obj = Student.objects.get_or_create(user=user)
					# Set/update all fields
					student.roll = row.get('roll')
					student.name = row.get('name')
					student.department = row.get('department')
					# Convert to int if possible, else use default
					def to_int(val, default=None):
						try:
							return int(val)
						except (TypeError, ValueError):
							return default
					student.semester = to_int(row.get('semester'), 1)
					student.year = to_int(row.get('year'), 1)
					student.section = to_int(row.get('section'), 2)
					student.address = row.get('address')
					student.mobile = to_int(row.get('mobile'))
					student.parent_mobile = to_int(row.get('parent_mobile'))
					# Parse date
					dob_val = row.get('dob')
					if dob_val:
						try:
							student.dob = datetime.strptime(dob_val, "%Y-%m-%d").date()
						except Exception:
							student.dob = None
					else:
						student.dob = None
					student.age = to_int(row.get('age'))
					# Set batch and academic_year if present in CSV
					batch_start = row.get('batch_start')
					if batch_start and batch_start.isdigit():
						student.batch = f"{batch_start}-{int(batch_start)+4}"
					academic_start = row.get('academic_start')
					if academic_start and academic_start.isdigit():
						student.academic_year = f"{academic_start}-{int(academic_start)+2}"
					student.save()
					if created_obj:
						created += 1
					else:
						updated += 1
				messages.success(request, f"Imported {created} students, updated {updated} students.")
				return redirect("..")
		else:
			form = StudentImportForm()
		return render(request, "admin/core/import_students.html", {"form": form})

class StaffAdmin(admin.ModelAdmin):
		list_display = ('user', 'name', 'department', 'position', 'position2', 'position3')
		list_filter = ('department', 'position', 'position2', 'position3')
		search_fields = ('name', 'user__username')
		list_editable = ('position',)
		# Add PET Staff to position choices in the admin form
		def formfield_for_choice_field(self, db_field, request, **kwargs):
			if db_field.name == "position":
				choices = list(db_field.choices)
				if ("PET Staff", "PET Staff") not in choices:
					choices.append(("PET Staff", "PET Staff"))
				kwargs["choices"] = choices
			return super().formfield_for_choice_field(db_field, request, **kwargs)

admin.site.register(Staff, StaffAdmin)
admin.site.register(OD)
admin.site.register(LEAVE)
admin.site.register(GATEPASS)
admin.site.register(BONAFIDE)
admin.site.register(HOD)
# Register new Sports OD models
admin.site.register(SportsOD)
admin.site.register(SportsODPlayer)
class AHODAdmin(admin.ModelAdmin):
	list_display = ('user', 'department')
	list_filter = ('department',)

	actions = ['set_position2_ahod']

	def set_position2_ahod(self, request, queryset):
		# Set position2 to Assistant Head of the Department (1) for all linked staff
		updated = 0
		for ahod in queryset:
			if ahod.user:
				ahod.user.position2 = 1  # 1 = Assistant Head of the Department
				ahod.user.save()
				updated += 1
		self.message_user(request, f"Set position2 as Assistant Head of the Department for {updated} staff.")
	set_position2_ahod.short_description = 'Set position2 as Assistant Head of the Department for selected AHODs'

admin.site.register(AHOD, AHODAdmin)
admin.site.register(StaffRating)
admin.site.register(RatingQuestions)
admin.site.register(IndividualStaffRating)

admin.site.register(SpotFeedback)

# Register Attendance only
class SemesterSubjectInline(admin.TabularInline):
	model = SemesterSubject
	extra = 1

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
	inlines = [SemesterSubjectInline]
	list_display = ("department", "semester")
	search_fields = ("department__name", "semester")


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
	# Only the poster image and published flag are relevant for homepage posters
	list_display = ('has_image', 'published')
	list_filter = ('published',)
	fields = ('image', 'published')
	actions = ['make_published', 'make_unpublished']

	def has_image(self, obj):
		return bool(obj.image)
	has_image.boolean = True
	has_image.short_description = 'Has Poster'

	def make_published(self, request, queryset):
		from django.utils import timezone
		updated = queryset.update(published=True, publish_date=timezone.now())
		self.message_user(request, f"Marked {updated} notices as published.")
	make_published.short_description = 'Mark selected notices as published'

	def make_unpublished(self, request, queryset):
		updated = queryset.update(published=False, publish_date=None)
		self.message_user(request, f"Marked {updated} notices as unpublished.")
	make_unpublished.short_description = 'Mark selected notices as unpublished'


@admin.register(Circular)
class CircularAdmin(admin.ModelAdmin):
	# Hide `title` and `subject` from admin list and form per request
	list_display = ('reference_no', 'from_text', 'to_text', 'target', 'published', 'publish_date', 'created_by')
	list_filter = ('target', 'published', 'publish_date')
	exclude = ('title', 'subject')
	actions = ['make_published', 'make_unpublished']

	def make_published(self, request, queryset):
		from django.utils import timezone
		from .models import Notification, Student, Staff
		updated = queryset.update(published=True, publish_date=timezone.now())
		# For each circular, create notifications for the intended audience
		created_count = 0
		for c in queryset:
			msg = f"Circular: [{c.id}] {c.title}"
			if c.target == 'students' or c.target == 'all':
				students = Student.objects.all()
				notes = []
				for s in students:
					# avoid duplicate notifications
					if not Notification.objects.filter(student=s, message__icontains=f"Circular: [{c.id}]").exists():
						notes.append(Notification(student=s, message=msg, circular=c))
				Notification.objects.bulk_create(notes)
				created_count += len(notes)
			if c.target == 'staff' or c.target == 'all':
				staffs = Staff.objects.all()
				notes = []
				for st in staffs:
					if not Notification.objects.filter(staff=st, message__icontains=f"Circular: [{c.id}]").exists():
						notes.append(Notification(staff=st, message=msg, circular=c))
				Notification.objects.bulk_create(notes)
				created_count += len(notes)
		self.message_user(request, f"Marked {updated} circulars as published. Created {created_count} notifications.")
	make_published.short_description = 'Mark selected circulars as published'

	def make_unpublished(self, request, queryset):
		from .models import Notification
		# Remove previously created notifications for these circulars
		for c in queryset:
			msg_snippet = f"Circular: [{c.id}]"
			Notification.objects.filter(message__icontains=msg_snippet).delete()
		updated = queryset.update(published=False, publish_date=None)
		self.message_user(request, f"Marked {updated} circulars as unpublished and removed related notifications.")
	make_unpublished.short_description = 'Mark selected circulars as unpublished'

	def save_model(self, request, obj, form, change):
		# When saving via admin form, ensure post-save logic runs and report counts
		super().save_model(request, obj, form, change)
		# If published, ensure notifications exist (post_save handles creation); inform admin
		if obj.published:
			from .models import Notification
			cnt = Notification.objects.filter(circular=obj).count()
			self.message_user(request, f"Circular saved. {cnt} notification(s) are associated with this circular.")