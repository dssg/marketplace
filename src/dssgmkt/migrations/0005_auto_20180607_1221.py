# Generated by Django 2.0.6 on 2018-06-07 17:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dssgmkt', '0004_auto_20180607_1217'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='organizationrole',
            unique_together={('user', 'organization')},
        ),
    ]