# Generated by Django 2.0.6 on 2018-06-14 20:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0007_auto_20180614_1500'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organization',
            name='logo',
        ),
        migrations.AddField(
            model_name='organization',
            name='logo_url',
            field=models.URLField(blank=True, help_text='Upload an image file that represents your organization', null=True, verbose_name='Organization logo'),
        ),
    ]
