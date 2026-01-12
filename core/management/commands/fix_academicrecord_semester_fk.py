from django.core.management.base import BaseCommand
from core.models import Semester
from django.db import transaction

class Command(BaseCommand):
    help = 'AcademicRecord model removed; no action needed.'

    def handle(self, *args, **options):
    # AcademicRecord model removed; no action needed.
