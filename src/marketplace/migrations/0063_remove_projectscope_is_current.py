# Generated by Django 2.0.6 on 2018-07-31 20:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0062_auto_20180730_1232'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='projectscope',
            name='is_current',
        ),
    ]
