from django.core.management.base import BaseCommand
# AcademicRecord model removed

class Command(BaseCommand):
    help = 'Delete all AcademicRecord rows (for migration recovery)'

    def handle(self, *args, **options):
        count = AcademicRecord.objects.count()
        AcademicRecord.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Deleted {count} AcademicRecord(s).'))
