# Generated by Django 2.1.4 on 2020-03-20 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plugins', '0010_auto_20200212_1808'),
    ]

    operations = [
        migrations.AddField(
            model_name='pluginparameter',
            name='short_flag',
            field=models.CharField(blank=True, max_length=52),
        ),
    ]