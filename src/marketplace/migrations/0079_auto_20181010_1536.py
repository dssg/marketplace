# Generated by Django 2.0.9 on 2018-10-10 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0078_organization_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='initial_type',
            field=models.IntegerField(choices=[(0, 'Site staff'), (1, 'Volunteer'), (2, 'Organization member')], default=1, help_text='Users can check their preference when they sign up to indicate they want to be volunteers or create/join organizations', null=True, verbose_name='Initial type of user'),
        ),
    ]
