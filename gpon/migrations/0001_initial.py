# Generated by Django 4.1.7 on 2023-09-25 11:22

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("check", "0026_alter_devicemedia_description"),
    ]

    operations = [
        migrations.CreateModel(
            name="Address",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "region",
                    models.CharField(
                        default="Севастополь", max_length=128, verbose_name="Регион"
                    ),
                ),
                (
                    "settlement",
                    models.CharField(
                        default="Севастополь",
                        help_text="Любимовка, Верхнесадовое",
                        max_length=128,
                        verbose_name="Населенный пункт",
                    ),
                ),
                (
                    "plan_structure",
                    models.CharField(
                        help_text="Рыбак-7",
                        max_length=128,
                        null=True,
                        verbose_name="ТСН СНТ, СТ",
                    ),
                ),
                (
                    "street",
                    models.CharField(
                        help_text="Полное название с указанием типа (улица/проспект/проезд/бульвар/шоссе/переулок/тупик)",
                        max_length=128,
                        null=True,
                        verbose_name="Улица",
                    ),
                ),
                (
                    "house",
                    models.CharField(
                        help_text="Можно с буквой (русской)",
                        max_length=16,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^\\d+[а-яА-Я]?$", message="Неверный формат дома"
                            )
                        ],
                        verbose_name="Дом",
                    ),
                ),
                (
                    "block",
                    models.PositiveSmallIntegerField(
                        null=True,
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name="Корпус",
                    ),
                ),
                ("floor", models.SmallIntegerField(null=True, verbose_name="Этаж")),
                (
                    "apartment",
                    models.PositiveSmallIntegerField(
                        null=True,
                        validators=[django.core.validators.MinValueValidator(1)],
                        verbose_name="Квартира",
                    ),
                ),
            ],
            options={
                "db_table": "gpon_addresses",
            },
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("person", "Person"),
                            ("company", "Company"),
                            ("contract", "Contract"),
                        ],
                        max_length=128,
                    ),
                ),
                (
                    "company_name",
                    models.CharField(blank=True, max_length=256, null=True),
                ),
                ("first_name", models.CharField(blank=True, max_length=256, null=True)),
                ("surname", models.CharField(blank=True, max_length=256, null=True)),
                ("last_name", models.CharField(blank=True, max_length=256, null=True)),
                ("phone", models.CharField(blank=True, max_length=20, null=True)),
                ("contract", models.CharField(max_length=128)),
            ],
            options={
                "db_table": "gpon_customers",
            },
        ),
        migrations.CreateModel(
            name="End3",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("location", models.CharField(max_length=255)),
                (
                    "type",
                    models.CharField(
                        choices=[("sp", "Splitter"), ("rz", "Rizer")],
                        max_length=2,
                        verbose_name="Тип оконечного оборудования",
                    ),
                ),
                (
                    "capacity",
                    models.PositiveSmallIntegerField(
                        choices=[(2, 2), (4, 4), (8, 8), (16, 16), (24, 24)],
                        help_text="Кол-во портов/волокон",
                    ),
                ),
                (
                    "address",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="end3_set",
                        to="gpon.address",
                    ),
                ),
            ],
            options={
                "db_table": "gpon_end3",
            },
        ),
        migrations.CreateModel(
            name="HouseB",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "apartment_building",
                    models.BooleanField(help_text="Многоквартирный дом или частный"),
                ),
                (
                    "floors",
                    models.PositiveSmallIntegerField(
                        help_text="кол-во этажей",
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                (
                    "total_entrances",
                    models.PositiveSmallIntegerField(
                        help_text="Кол-во подъездов",
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(255),
                        ],
                    ),
                ),
                (
                    "address",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="buildings",
                        to="gpon.address",
                    ),
                ),
                (
                    "end3_set",
                    models.ManyToManyField(related_name="house", to="gpon.end3"),
                ),
            ],
            options={
                "db_table": "gpon_houses_buildings",
            },
        ),
        migrations.CreateModel(
            name="HouseOLTState",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("entrances", models.CharField(max_length=25)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "house",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="gpon.houseb"
                    ),
                ),
            ],
            options={
                "db_table": "gpon_house_olt_state",
            },
        ),
        migrations.CreateModel(
            name="Service",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=128)),
            ],
            options={
                "db_table": "gpon_services",
            },
        ),
        migrations.CreateModel(
            name="TechCapability",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("reserved", "Reserved"),
                            ("pause", "Pause"),
                            ("empty", "Empty"),
                            ("bad", "Bad"),
                        ],
                        default="empty",
                        max_length=16,
                    ),
                ),
                (
                    "splitter_port",
                    models.PositiveSmallIntegerField(
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(24),
                        ],
                        verbose_name="Порт на сплиттере",
                    ),
                ),
                (
                    "rizer_fiber",
                    models.CharField(
                        max_length=128,
                        null=True,
                        verbose_name="Цвет волокна на райзере",
                    ),
                ),
                (
                    "end3",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="gpon.end3"
                    ),
                ),
            ],
            options={
                "db_table": "gpon_tech_capabilities",
            },
        ),
        migrations.CreateModel(
            name="SubscriberConnection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("ip", models.GenericIPAddressField(null=True, protocol="ipv4")),
                ("ont_id", models.PositiveSmallIntegerField()),
                ("ont_serial", models.CharField(max_length=128, null=True)),
                ("ont_mac", models.CharField(max_length=12, null=True)),
                ("order", models.CharField(max_length=128, null=True)),
                ("transit", models.PositiveIntegerField(null=True)),
                ("connected_at", models.DateTimeField(null=True)),
                (
                    "address",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="subscribers",
                        to="gpon.address",
                    ),
                ),
                (
                    "services",
                    models.ManyToManyField(
                        related_name="subscribers", to="gpon.service"
                    ),
                ),
                (
                    "tech_capability",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="gpon.techcapability",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="OLTState",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("olt_port", models.CharField(max_length=24)),
                ("fiber", models.CharField(blank=True, max_length=100, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "device",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="check.devices",
                    ),
                ),
                (
                    "houses",
                    models.ManyToManyField(
                        related_name="olt_states",
                        through="gpon.HouseOLTState",
                        to="gpon.houseb",
                    ),
                ),
            ],
            options={
                "db_table": "gpon_olt_states",
            },
        ),
        migrations.AddField(
            model_name="houseoltstate",
            name="statement",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="gpon.oltstate",
            ),
        ),
    ]
