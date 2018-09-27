# Generated by Django 2.0.6 on 2018-07-24 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0052_projectdiscussionchannel_related_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectdiscussionchannel',
            name='description',
            field=models.TextField(blank=True, help_text='Description of the purpose of this discussion channel.', max_length=200, null=True, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='projectdiscussionchannel',
            name='is_read_only',
            field=models.BooleanField(default=False, help_text='Specifies if this channel has been archived and is read only.', verbose_name='Read only channel'),
        ),
    ]
