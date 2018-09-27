# Generated by Django 2.0.6 on 2018-07-10 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0020_auto_20180710_1106'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usernotification',
            name='severity',
            field=models.IntegerField(choices=[(0, 'Information'), (1, 'Warning'), (2, 'Error'), (3, 'Critical')], default=0),
        ),
    ]
