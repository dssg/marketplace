# Generated by Django 2.0.6 on 2018-07-24 01:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0050_auto_20180722_2112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='skill',
            name='area',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='skill',
            name='name',
            field=models.CharField(max_length=100),
        ),
    ]
