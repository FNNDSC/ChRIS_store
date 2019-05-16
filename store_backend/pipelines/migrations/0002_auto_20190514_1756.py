# Generated by Django 2.1.4 on 2019-05-14 17:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pipelines', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pipeline',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
