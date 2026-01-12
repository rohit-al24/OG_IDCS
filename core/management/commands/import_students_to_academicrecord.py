from django.core.management.base import BaseCommand
from core.models import Student, Semester

class Command(BaseCommand):
    help = 'Import all students from core_student to core_academicrecord (one record per student, semester left blank).'

    def handle(self, *args, **options):
        count = 0
        from core.models import Department
        for student in Student.objects.all():
            # Try to match department by code or name
            dept_obj = Department.objects.filter(code=student.department).first()
            if not dept_obj:
                dept_obj = Department.objects.filter(name=student.department).first()
            if not dept_obj:
                self.stdout.write(self.style.WARNING(f"No Department found for {student.name} ({student.department})"))
                continue
            semester_obj = Semester.objects.filter(
                department=dept_obj,
                semester_number=student.semester
            ).first()
            if not semester_obj:
                self.stdout.write(self.style.WARNING(f"No Semester found for {student.name} ({dept_obj}, Sem {student.semester})"))
                continue
            # Only create if not already present for this student and semester
            if not AcademicRecord.objects.filter(student=student, semester=semester_obj).exists():
        # AcademicRecord creation removed
    self.stdout.write(self.style.SUCCESS(f'AcademicRecord import skipped (model removed).'))
