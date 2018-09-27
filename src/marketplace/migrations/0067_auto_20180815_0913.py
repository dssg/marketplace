# Generated by Django 2.0.6 on 2018-08-15 14:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0066_auto_20180802_1049'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='projecttaskrequirement',
            options={'ordering': ['-level']},
        ),
        migrations.AlterModelOptions(
            name='volunteerskill',
            options={'ordering': ['skill__area', '-level']},
        ),
        migrations.RemoveField(
            model_name='project',
            name='available_data',
        ),
        migrations.RemoveField(
            model_name='project',
            name='challenges',
        ),
        migrations.RemoveField(
            model_name='project',
            name='scoping_process',
        ),
        migrations.RemoveField(
            model_name='projectscope',
            name='available_data',
        ),
        migrations.RemoveField(
            model_name='projectscope',
            name='available_staff',
        ),
        migrations.RemoveField(
            model_name='projectscope',
            name='project_impact',
        ),
        migrations.RemoveField(
            model_name='projectscope',
            name='scope',
        ),
        migrations.RemoveField(
            model_name='projectscope',
            name='scoping_process',
        ),
        migrations.AddField(
            model_name='project',
            name='scope_analysis',
            field=models.TextField(blank=True, help_text='Describe the internal process for scoping and implementing this project (Who are the stakeholders, what discussions have already happened, etc.)', max_length=5000, null=True, verbose_name='Scope: analysis needed'),
        ),
        migrations.AddField(
            model_name='project',
            name='scope_available_data',
            field=models.TextField(blank=True, help_text='Describe the data available to use for this project. (Size, variables, completeness, availability, privacy, etc.)', max_length=5000, null=True, verbose_name='Scope: data'),
        ),
        migrations.AddField(
            model_name='project',
            name='scope_goals',
            field=models.TextField(blank=True, help_text='Describe the internal process for scoping and implementing this project (Who are the stakeholders, what discussions have already happened, etc.)', max_length=5000, null=True, verbose_name='Scope: project goal(s)'),
        ),
        migrations.AddField(
            model_name='project',
            name='scope_implementation',
            field=models.TextField(blank=True, help_text='Who from your organization would be available to provide assistance (approximately 1-3 hours per week) throughout the summer? (Technical staff, subject matter experts, etc.)', max_length=5000, null=True, verbose_name='Scope: implementation'),
        ),
        migrations.AddField(
            model_name='project',
            name='scope_interventions',
            field=models.TextField(blank=True, help_text='Describe the internal process for scoping and implementing this project (Who are the stakeholders, what discussions have already happened, etc.)', max_length=5000, null=True, verbose_name='Scope: interventions and actions'),
        ),
        migrations.AddField(
            model_name='project',
            name='scope_validation_methodology',
            field=models.TextField(blank=True, help_text='Describe the internal process for scoping and implementing this project (Who are the stakeholders, what discussions have already happened, etc.)', max_length=5000, null=True, verbose_name='Scope: validation methodology'),
        ),
        migrations.AddField(
            model_name='project',
            name='stakeholders',
            field=models.TextField(blank=True, help_text='List the main challenges that you foresee in the project implementation. Remember to frame them so volunteers understand that this is an exciting project.', max_length=5000, null=True, verbose_name='Internal stakeholders'),
        ),
        migrations.AddField(
            model_name='projectscope',
            name='scope_analysis',
            field=models.TextField(blank=True, help_text='Describe the internal process for scoping and implementing this project (Who are the stakeholders, what discussions have already happened, etc.)', max_length=5000, null=True, verbose_name='Scope: analysis needed'),
        ),
        migrations.AddField(
            model_name='projectscope',
            name='scope_available_data',
            field=models.TextField(blank=True, help_text='Describe the data available to use for this project. (Size, variables, completeness, availability, privacy, etc.)', max_length=5000, null=True, verbose_name='Scope: data'),
        ),
        migrations.AddField(
            model_name='projectscope',
            name='scope_goals',
            field=models.TextField(blank=True, help_text='Describe the internal process for scoping and implementing this project (Who are the stakeholders, what discussions have already happened, etc.)', max_length=5000, null=True, verbose_name='Scope: project goal(s)'),
        ),
        migrations.AddField(
            model_name='projectscope',
            name='scope_implementation',
            field=models.TextField(blank=True, help_text='Who from your organization would be available to provide assistance (approximately 1-3 hours per week) throughout the summer? (Technical staff, subject matter experts, etc.)', max_length=5000, null=True, verbose_name='Scope: implementation'),
        ),
        migrations.AddField(
            model_name='projectscope',
            name='scope_interventions',
            field=models.TextField(blank=True, help_text='Describe the internal process for scoping and implementing this project (Who are the stakeholders, what discussions have already happened, etc.)', max_length=5000, null=True, verbose_name='Scope: interventions and actions'),
        ),
        migrations.AddField(
            model_name='projectscope',
            name='scope_validation_methodology',
            field=models.TextField(blank=True, help_text='Describe the internal process for scoping and implementing this project (Who are the stakeholders, what discussions have already happened, etc.)', max_length=5000, null=True, verbose_name='Scope: validation methodology'),
        ),
        migrations.AlterField(
            model_name='project',
            name='available_staff',
            field=models.TextField(blank=True, help_text='List the main challenges that you foresee in the project implementation. Remember to frame them so volunteers understand that this is an exciting project.', max_length=5000, null=True, verbose_name='Internal people available during the project'),
        ),
        migrations.AlterField(
            model_name='project',
            name='motivation',
            field=models.TextField(blank=True, help_text='Explain what is the context in which the project is needed, what is the motivation behind the project, and what are the goals of the project', max_length=5000, null=True, verbose_name='Background and motivation'),
        ),
        migrations.AlterField(
            model_name='project',
            name='project_impact',
            field=models.TextField(blank=True, help_text="How critical is this project for your organization? How you're solving this problem today? What's the impact if this project is completed successfully?", max_length=5000, null=True, verbose_name='Intended impact'),
        ),
        migrations.AlterField(
            model_name='project',
            name='solution_description',
            field=models.TextField(blank=True, help_text='Describe what is the solution to the problem that will be build/created/deployed during this project.', max_length=5000, null=True, verbose_name='Project description'),
        ),
    ]
