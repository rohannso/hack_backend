# Generated by Django 5.1.7 on 2025-04-05 23:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('path', '0004_learningpath_status_alter_learningpath_path_data_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='learningpath',
            name='status',
        ),
    ]
