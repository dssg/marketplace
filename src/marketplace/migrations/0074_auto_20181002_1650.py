# Generated by Django 2.0.6 on 2018-10-02 21:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0073_manual_20181001_1334'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserTaskPreference',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preference', models.CharField(choices=[('SCT', 'Project scoping'), ('PMT', 'Project management'), ('DWT', 'Domain work'), ('QAT', 'QA')], default='SCT', help_text='Choose what type of tasks you are interested in working in.', max_length=3, verbose_name='Task type')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
        ),
        migrations.AlterField(
            model_name='projecttask',
            name='type',
            field=models.CharField(choices=[('SCT', 'Project scoping'), ('PMT', 'Project management'), ('DWT', 'Domain work'), ('QAT', 'QA')], default='SCT', help_text='Different types of tasks have different roles within the project. Scoping tasks are needed to help new projects define the work that needs to be done. Project management tasks are used to guide the project from inception to finish. Domain work tasks include any data science work specified in the project.', max_length=3, verbose_name='Task type'),
        ),
        migrations.AlterUniqueTogether(
            name='usertaskpreference',
            unique_together={('preference', 'user')},
        ),
    ]