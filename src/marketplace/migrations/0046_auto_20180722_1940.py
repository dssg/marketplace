# Generated by Django 2.0.6 on 2018-07-23 00:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0045_volunteerprofile_creation_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projecttaskrole',
            name='role',
            field=models.IntegerField(choices=[(0, 'Volunteer'), (0, 'Staff')], default=0, verbose_name='User role'),
        ),
    ]
