# Generated by Django 4.1.4 on 2023-01-18 09:19

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("check", "0023_interfacescomments"),
    ]

    operations = [
        migrations.AddField(
            model_name="interfacescomments",
            name="datetime",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]
