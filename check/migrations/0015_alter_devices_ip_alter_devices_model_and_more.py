# Generated by Django 4.0.7 on 2022-08-29 07:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("check", "0014_alter_devices_model_alter_devices_vendor"),
    ]

    operations = [
        migrations.AlterField(
            model_name="devices",
            name="ip",
            field=models.GenericIPAddressField(
                help_text="ipv4", protocol="ipv4", unique=True, verbose_name="IP адрес"
            ),
        ),
        migrations.AlterField(
            model_name="devices",
            name="model",
            field=models.CharField(
                blank=True,
                help_text="Если не указано, то обновится автоматически при подключении к устройству",
                max_length=100,
                null=True,
                verbose_name="Модель",
            ),
        ),
        migrations.AlterField(
            model_name="devices",
            name="name",
            field=models.CharField(
                help_text="Уникальное поле",
                max_length=100,
                unique=True,
                verbose_name="Имя оборудования",
            ),
        ),
        migrations.AlterField(
            model_name="devices",
            name="snmp_community",
            field=models.CharField(
                blank=True,
                help_text="Версия - v2c",
                max_length=64,
                null=True,
                verbose_name="SNMP community",
            ),
        ),
        migrations.AlterField(
            model_name="devices",
            name="vendor",
            field=models.CharField(
                blank=True,
                help_text="Если не указано, то обновится автоматически при подключении к устройству",
                max_length=100,
                null=True,
                verbose_name="Производитель",
            ),
        ),
    ]
