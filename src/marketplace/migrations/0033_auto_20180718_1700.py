# Generated by Django 2.0.6 on 2018-07-18 22:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0032_auto_20180718_1642'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationmembershiprequest',
            name='reviewer',
            field=models.ForeignKey(default=1, help_text='User that reviewed the membership application', on_delete=django.db.models.deletion.CASCADE, related_name='reviewed_organization_membership_request', to=settings.AUTH_USER_MODEL, verbose_name='Review author'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='projecttaskreview',
            name='review_score',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Needs improvement'), (2, 'Fair'), (3, 'Good'), (4, 'Excellent'), (5, 'Outstanding')], default=1, help_text='What do you think about the quality of work in this task?', verbose_name='Score'),
        ),
        migrations.AddField(
            model_name='projecttaskreview',
            name='reviewer',
            field=models.ForeignKey(default=1, help_text='The user that did the QA review of this task.', on_delete=django.db.models.deletion.CASCADE, related_name='reviewed_project_task', to=settings.AUTH_USER_MODEL, verbose_name='Review author'),
            preserve_default=False,
        ),
    ]
