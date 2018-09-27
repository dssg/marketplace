# Generated by Django 2.0.6 on 2018-07-13 20:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0027_projectscope'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectscope',
            name='available_data',
            field=models.TextField(blank=True, help_text='Describe the data available to use for this project. (Size, variables, completeness, availability, privacy, etc.)', max_length=5000, null=True, verbose_name='Available data'),
        ),
        migrations.AddField(
            model_name='projectscope',
            name='available_staff',
            field=models.TextField(blank=True, help_text='Who from your organization would be available to provide assistance (approximately 1-3 hours per week) throughout the summer? (Technical staff, subject matter experts, etc.)', max_length=5000, null=True, verbose_name='Available staff'),
        ),
        migrations.AddField(
            model_name='projectscope',
            name='project_impact',
            field=models.TextField(blank=True, help_text="How critical is this project for your organization? How you're solving this problem today? What's the impact if this project is completed successfully?", max_length=5000, null=True, verbose_name='Project impact'),
        ),
        migrations.AddField(
            model_name='projectscope',
            name='scoping_process',
            field=models.TextField(blank=True, help_text='Describe the internal process for scoping and implementing this project (Who are the stakeholders, what discussions have already happened, etc.)', max_length=5000, null=True, verbose_name='Scoping process'),
        ),
        migrations.AlterField(
            model_name='projectlog',
            name='change_target',
            field=models.CharField(blank=True, choices=[('TK', 'Task'), ('VA', 'Volunteer application'), ('ST', 'Staff'), ('TK', 'Task review'), ('VO', 'Volunteer'), ('SU', 'Status'), ('IN', 'Information'), ('SC', 'Scope')], default='TK', max_length=2, null=True),
        ),
    ]
