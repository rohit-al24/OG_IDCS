from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('feed360', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedbackresponse',
            name='sentiment_label',
            field=models.CharField(max_length=16, blank=True, null=True),
        ),
    ]
