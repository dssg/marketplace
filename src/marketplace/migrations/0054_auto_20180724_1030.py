# Generated by Django 2.0.6 on 2018-07-24 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0053_auto_20180724_0921'),
    ]

    operations = [
        migrations.AlterField(
            model_name='volunteerprofile',
            name='degree_level',
            field=models.IntegerField(blank=True, choices=[(0, 'Other'), (1, 'Primary education'), (2, 'Secondary education'), (3, "Bachelor's"), (4, "Master's"), (5, 'PhD')], default=3, help_text='The level of the highest level degree you have.', null=True, verbose_name='Degree level'),
        ),
    ]
