# Generated by Django 2.0.6 on 2018-07-21 16:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0041_auto_20180720_1531'),
    ]

    operations = [
        migrations.CreateModel(
            name='PinnedTaskReview',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_review', models.ForeignKey(help_text='Project task review this pinned review is holding.', on_delete=django.db.models.deletion.CASCADE, to='marketplace.ProjectTaskReview', verbose_name='Task review')),
                ('user', models.ForeignKey(help_text='The volunteer pinning the review.', on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Volunteer')),
            ],
        ),
    ]
