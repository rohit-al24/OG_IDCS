# Generated migration for splitting sections into three ForeignKeys in SemesterSubject
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0095_merge_20250923_2101'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='semestersubject',
            name='sections',
        ),
        migrations.AddField(
            model_name='semestersubject',
            name='section1',
            field=models.ForeignKey(blank=True, help_text='First section for this subject.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subject_section1', to='core.section'),
        ),
        migrations.AddField(
            model_name='semestersubject',
            name='section2',
            field=models.ForeignKey(blank=True, help_text='Second section for this subject.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subject_section2', to='core.section'),
        ),
        migrations.AddField(
            model_name='semestersubject',
            name='section3',
            field=models.ForeignKey(blank=True, help_text='Third section for this subject.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subject_section3', to='core.section'),
        ),
    ]
