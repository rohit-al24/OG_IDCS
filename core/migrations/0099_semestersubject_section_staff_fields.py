# Migration to add staff1, staff2, staff3 to SemesterSubject and remove staff
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0098_semestersubject_section_fields_to_choices'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='semestersubject',
            name='staff',
        ),
        migrations.AddField(
            model_name='semestersubject',
            name='staff1',
            field=models.ForeignKey(blank=True, help_text='Staff for section 1', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='semester_subject_staff1', to='core.staff'),
        ),
        migrations.AddField(
            model_name='semestersubject',
            name='staff2',
            field=models.ForeignKey(blank=True, help_text='Staff for section 2', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='semester_subject_staff2', to='core.staff'),
        ),
        migrations.AddField(
            model_name='semestersubject',
            name='staff3',
            field=models.ForeignKey(blank=True, help_text='Staff for section 3', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='semester_subject_staff3', to='core.staff'),
        ),
    ]
