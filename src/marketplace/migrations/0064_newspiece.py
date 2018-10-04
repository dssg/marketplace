# Generated by Django 2.0.6 on 2018-08-02 15:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0063_remove_projectscope_is_current'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsPiece',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Title')),
                ('contents', models.TextField(max_length=2000, verbose_name='News contents')),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('last_modified_date', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]