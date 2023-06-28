import orjson
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from check import models
from app_settings.models import LogsElasticStackSettings
from devicemanager.device import DeviceManager
from devicemanager.device import Interfaces as InterfacesObject, ZabbixAPIConnection
from net_tools.models import DevicesInfo as ModelDeviceInfo
from check.interfaces_collector import DeviceInterfacesCollectorMixin
from ..decorators import except_connection_errors
from ..permissions import DevicePermission
from ..filters import DeviceFilter, DeviceInfoFilter
from ..serializers import DevicesSerializer
from ..swagger.schemas import (
    devices_interfaces_workload_list_api_doc,
    interfaces_workload_api_doc,
    interfaces_list_api_doc,
)


class DevicesListAPIView(generics.ListAPIView):
    """
    ## Этот класс представляет собой ListAPIView, который возвращает список всех устройств в базе данных.
    """

    serializer_class = DevicesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DeviceFilter

    def get_queryset(self):
        """
        ## Возвращаем queryset всех устройств из доступных для пользователя групп
        """

        # Фильтруем запрос
        group_ids = self.request.user.profile.devices_groups.all().values_list("id", flat=True)
        return models.Devices.objects.filter(group_id__in=group_ids).select_related("group")

    def get(self, request, *args, **kwargs):
        """
        ## Возвращаем список всех устройств, без пагинации

        Пример ответа:

            [
                {
                    "ip": "172.30.0.58",
                    "name": "FTTB_Aktybinsk42_p1_TKD_116",
                    "vendor": "D-Link",
                    "group": "ASW",
                    "model": "DES-3200-28",
                    "port_scan_protocol": "telnet"
                },

                ...

            ]
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@method_decorator(devices_interfaces_workload_list_api_doc, name="get")
class AllDevicesInterfacesWorkLoadAPIView(generics.ListAPIView):
    serializer_class = DevicesSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = DeviceInfoFilter

    def get_queryset(self):
        """
        ## Возвращаем queryset всех устройств из доступных для пользователя групп
        """

        # Фильтруем запрос
        group_ids = self.request.user.profile.devices_groups.all().values_list("id", flat=True)
        return (
            ModelDeviceInfo.objects.filter(dev__group_id__in=group_ids)
            .select_related("dev")
            .order_by("dev__name")
        )

    @staticmethod
    def get_interfaces_load(device: ModelDeviceInfo):
        interfaces = InterfacesObject(orjson.loads(device.interfaces or "[]")).physical()

        non_system = interfaces.non_system()
        abons_up = non_system.up()
        abons_up_with_desc = abons_up.with_description()
        abons_down = non_system.down()
        abons_down_with_desc = abons_down.with_description()

        return {
            "count": interfaces.count,
            "abons": non_system.count,
            "abons_up": abons_up.count,
            "abons_up_with_desc": abons_up_with_desc.count,
            "abons_up_no_desc": abons_up.count - abons_up_with_desc.count,
            "abons_down": abons_down.count,
            "abons_down_with_desc": abons_down_with_desc.count,
            "abons_down_no_desc": abons_down.count - abons_down_with_desc.count,
        }

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        response_data = {
            "devices_count": queryset.count(),
            "devices": [
                {
                    "interfaces_count": self.get_interfaces_load(dev_info),
                    **DevicesSerializer(dev_info.dev).data,
                }
                for dev_info in queryset
            ],
        }

        return Response(response_data)


@method_decorator(interfaces_workload_api_doc, name="get")
class DeviceInterfacesWorkLoadAPIView(
    generics.RetrieveAPIView, AllDevicesInterfacesWorkLoadAPIView
):
    lookup_url_kwarg = "device_name"
    lookup_field = "dev__name"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        result = self.get_interfaces_load(instance)
        return Response(result)


class DeviceInterfacesAPIView(DeviceInterfacesCollectorMixin, APIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    def get_device(self) -> models.Devices:
        """Получаем объект устройства из БД"""

        self.device = get_object_or_404(models.Devices, name=self.kwargs["device_name"])
        self.check_object_permissions(self.request, self.device)
        return self.device

    @interfaces_list_api_doc
    @except_connection_errors
    def get(self, request, *args, **kwargs):
        """
        ## Вывод интерфейсов оборудования

        Пример вывода:

            {
                "interfaces": [
                    {
                        "Interface": "gi1/0/1",
                        "Status": "up",
                        "Description": "To_DEVICE-1",
                        "Link": {
                            "device_name": "DEVICE-1",
                            "url": "/device/DEVICE-1"
                        },
                        "Comments": [
                            {
                                "text": "Какой-то комментарий",
                                "user": "irudenko",
                                "id": 14
                            }
                        ]
                    },

                    ...

                    {
                        "Interface": "te1/0/4",
                        "Status": "down",
                        "Description": ""
                    }
                ],
                "deviceAvailable": true,
                "collected": "2023-03-01T15:13:11.559175"
            }
        """

        self.get_device()

        self.device_collector = DeviceManager.from_model(self.device)

        available = self.device.available  # Оборудование доступно или нет

        # Сканируем интерфейсы в реальном времени?
        current_status = bool(request.GET.get("current_status", False)) and available > 0

        # Вместе с VLAN?
        self.with_vlans = (
            False if self.device_collector.protocol == "snmp" else request.GET.get("vlans") == "1"
        )

        # Если не нужен текущий статус интерфейсов, то отправляем прошлые данные
        if not current_status:
            last_interfaces, last_datetime = self.get_last_interfaces()

            self.add_comments(last_interfaces)
            self.add_devices_links(last_interfaces)

            return Response(
                {
                    "interfaces": last_interfaces,
                    "deviceAvailable": available > 0,
                    "collected": last_datetime,
                }
            )

        # Собираем состояние интерфейсов оборудования в данный момент.
        self.collect_current_interfaces()

        # Синхронизируем реальные данные оборудования и поля в базе.
        self.sync_device_info_to_db()

        # Обновляем данные в Zabbix.
        self.device_collector.push_zabbix_inventory()

        # Если не собрали интерфейсы.
        if not self.device_collector.interfaces:
            # Возвращает пустой список интерфейсов.
            return Response(
                {
                    "interfaces": [],
                    "deviceAvailable": available > 0,
                    "collected": timezone.now(),
                }
            )

        self.save_interfaces_to_db()

        interfaces = self.device_collector.interfaces.json()
        self.add_devices_links(interfaces)
        self.add_comments(interfaces)

        return Response(
            {
                "interfaces": interfaces,
                "deviceAvailable": available > 0,
                "collected": timezone.now(),
            }
        )

    @staticmethod
    def add_devices_links(interfaces: list) -> list:
        """
        ## Добавляет к интерфейсам ссылку на оборудование "Link", которое находится в описании

            {
                "Interface": "te1/0/2",
                "Status": "up",
                "Description": "To_DEVICE-1_pTe0/1|DF|",
                "Link": {
                    "device_name": "DEVICE-1",
                    "url": "/device/DEVICE-1"
                }
            },

        :param interfaces: Список интерфейсов
        :return: Список интерфейсов с добавлением ссылок
        """

        devices_names = models.Devices.objects.values("name").all()
        for intf in interfaces:
            for dev in devices_names:
                if dev["name"] in intf["Description"]:
                    intf["Link"] = {
                        "device_name": dev["name"],
                        "url": reverse("device_info", args=[dev["name"]]),
                    }

        return interfaces

    def add_comments(self, interfaces: list) -> list:
        """
        ## Берет список интерфейсов и добавляет к ним существующие комментарии

            {
                "Interface": "Eth0/0/6",
                "Status": "up",
                "Description": "Teplostroy",
                "Comments": [
                    {
                        "text": "Стоит медиаконвертор",
                        "user": "irudenko",
                        "id": 14
                    }
                ]
            },

        :param interfaces: список интерфейсов для добавления комментариев
        """

        interfaces_comments = self.device.interfacescomments_set.select_related("user")

        for intf in interfaces:
            intf["Comments"] = [
                {
                    "text": comment.comment,
                    "user": comment.user.username,
                    "id": comment.id,
                }
                for comment in interfaces_comments
                if comment.interface == intf["Interface"]
            ]

        return interfaces


class DeviceInfoAPIView(APIView):
    """
    ## Возвращаем общую информацию оборудования

    Пример вывода:

        {
            "deviceName": "DEVICE-NAME",
            "deviceIP": "10.10.10.10",
            "elasticStackLink": "URL",
            "zabbixHostID": "45632",
            "zabbixInfo": {
                "description": "ОПИСАНИЕ ОБОРУДОВАНИЯ В ZABBIX",
                "inventory": {
                    "type": "Eltex",
                    "type_full": "MES3324F 28-port 1G/10G Managed Switch",
                    "serialno_a": "",
                    "macaddress_a": "",
                    "hardware": "MES3324F 28-port 1G/10G Managed Switch",

                    ...

                    "model": "MES3324F",
                    "vendor": "Eltex"
                }
            },
            "permission": 3,
            "coords": [
                "23.322332",
                "32.233223"
            ]
        }

    """

    permission_classes = [IsAuthenticated, DevicePermission]

    def get(self, request, device_name: str):
        model_dev = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, model_dev)

        dev = DeviceManager(name=device_name)
        return Response(
            {
                "deviceName": device_name,
                "deviceIP": model_dev.ip,
                # Создание URL-адреса для запроса журналов Kibana.
                "elasticStackLink": LogsElasticStackSettings.load().query_kibana_url(
                    device=model_dev
                ),
                "zabbixHostID": int(dev.zabbix_info.hostid or 0),
                "zabbixURL": ZabbixAPIConnection.ZABBIX_URL,
                "zabbixInfo": {
                    "description": dev.zabbix_info.description,
                    "inventory": dev.zabbix_info.inventory.to_dict,
                },
                "permission": request.user.profile.perm_level,
                "coords": dev.zabbix_info.inventory.coordinates(),
            }
        )


class DeviceStatsInfoAPIView(APIView):
    """
    ## Возвращаем данные CPU, FLASH, RAM, TEMP

    Пример вывода:

        {
            "cpu": {
                "util": [
                    2
                ]
            },
            "ram": {
                "util": 15
            },
            "flash": {
                "util": 50
            },
            "temp": {
                "value": 43.5,
                "status": "normal"
            }
        }

    """

    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    def get(self, request, device_name: str):
        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        # Если оборудование недоступно
        if not device.available:
            return Response({"detail": "Device unavailable"}, status=500)

        with device.connect() as session:
            device_stats: dict = session.get_device_info() or {}
            return Response(device_stats)
