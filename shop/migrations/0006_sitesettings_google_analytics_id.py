# Generated by Django 5.1.4 on 2025-05-17 05:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0005_sitesettings_threads_url_sitesettings_youtube_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='google_analytics_id',
            field=models.CharField(blank=True, help_text='Google Analytics tracking ID (e.g., G-HL7GG88HT2)', max_length=50),
        ),
    ]
