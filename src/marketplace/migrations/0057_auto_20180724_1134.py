# Generated by Django 2.0.6 on 2018-07-24 16:34

from django.db import migrations, models
import marketplace.models.org


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0056_auto_20180724_1111'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='logo_file',
            field=models.ImageField(blank=True, help_text='Upload an image file that represents your organization', null=True, upload_to='orglogos/', validators=[marketplace.models.common.validate_image_size], verbose_name='Organization logo'),
        ),
    ]