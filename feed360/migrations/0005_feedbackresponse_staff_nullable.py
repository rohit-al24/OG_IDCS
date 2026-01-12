from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('feed360', '0004_staff_name_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedbackresponse',
            name='staff',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, to='core.staff'),
        ),
    ]
