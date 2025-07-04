# Generated by Django 5.0.6 on 2025-06-15 22:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='logentry',
            name='fish_type',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='logentry',
            name='tank_type',
            field=models.CharField(choices=[('freshwater', '淡水'), ('saltwater', '海水'), ('brackish', '汽水')], default='freshwater', max_length=20),
        ),
    ]
