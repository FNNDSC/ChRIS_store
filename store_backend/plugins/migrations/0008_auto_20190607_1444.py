# Generated by Django 2.1.4 on 2019-06-07 14:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plugins', '0007_auto_20190514_1546'),
    ]

    operations = [
        migrations.AddField(
            model_name='pluginparameter',
            name='ui_exposed',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='pluginparameter',
            name='optional',
            field=models.BooleanField(default=False),
        ),
    ]