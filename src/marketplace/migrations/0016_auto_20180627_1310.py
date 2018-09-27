# Generated by Django 2.0.6 on 2018-06-27 18:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0015_projectcomment'),
    ]

    operations = [
        migrations.RenameField(
            model_name='projecttaskreview',
            old_name='reviewer_comment',
            new_name='public_reviewer_comments',
        ),
        migrations.AddField(
            model_name='projecttaskreview',
            name='private_reviewer_notes',
            field=models.TextField(blank=True, help_text='Private notes about the task. These notes will be shared with the rest of the project staff but not with the volunteer or anybody else.', max_length=2000, null=True, verbose_name="Private reviewer's notes"),
        ),
    ]
