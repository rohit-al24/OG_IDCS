from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('feed360', '0003_merge_20250920_1832'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedbackform',
            name='staff_name',
            field=models.CharField(max_length=100, blank=True, null=True, help_text="Selected staff name for feedback linking"),
        ),
        migrations.AddField(
            model_name='feedbackform',
            name='staff_name_other',
            field=models.CharField(max_length=100, blank=True, null=True, help_text="Custom staff name if 'Others' selected"),
        ),
        migrations.AddField(
            model_name='feedbackquestion',
            name='staff_name',
            field=models.CharField(max_length=100, blank=True, null=True, help_text="Selected staff name for feedback linking"),
        ),
        migrations.AddField(
            model_name='feedbackquestion',
            name='staff_name_other',
            field=models.CharField(max_length=100, blank=True, null=True, help_text="Custom staff name if 'Others' selected"),
        ),
    ]
