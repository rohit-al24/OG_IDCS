# Migration to change SemesterSubject section fields to PositiveIntegerField with SECTION choices
from django.db import migrations, models
import core.constants

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0097_alter_section_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='semestersubject',
            name='section1',
            field=models.PositiveIntegerField(choices=core.constants.SECTION, null=True, blank=True, help_text='First section for this subject.'),
        ),
        migrations.AlterField(
            model_name='semestersubject',
            name='section2',
            field=models.PositiveIntegerField(choices=core.constants.SECTION, null=True, blank=True, help_text='Second section for this subject.'),
        ),
        migrations.AlterField(
            model_name='semestersubject',
            name='section3',
            field=models.PositiveIntegerField(choices=core.constants.SECTION, null=True, blank=True, help_text='Third section for this subject.'),
        ),
    ]
