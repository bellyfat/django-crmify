# Generated by Django 2.0.2 on 2018-02-25 22:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crmify', '0003_lead_last_synced'),
    ]

    operations = [
        migrations.AddField(
            model_name='lead',
            name='external_status',
            field=models.CharField(blank=True, default=None, max_length=200, null=True),
        ),
    ]