from django.core.management.base import BaseCommand
from core.models import Staff, Student

class Command(BaseCommand):
    help = 'Set all staff who are advisors to students as advisor (position2=4) and lecturer (position=3)'

    def handle(self, *args, **options):
        advisor_ids = Student.objects.values_list('advisor', flat=True).distinct()
        updated = 0
        for staff in Staff.objects.filter(id__in=advisor_ids):
            staff.position = 3  # Lecturer
            staff.position2 = 4 # Advisor
            staff.save()
            updated += 1
        self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated} staff as lecturer+advisor'))
