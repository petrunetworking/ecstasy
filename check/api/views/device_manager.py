from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from check import models
from check.logging import log
from check.permissions import profile_permission
from check.services.device.interfaces import (
    change_port_state,
    set_interface_description,
    get_mac_addresses_on_interface,
    get_interface_detail_info,
    check_user_interface_permission,
)
from devicemanager.remote.exceptions import InvalidMethod
from ecstasy_project.types.api import UserAuthenticatedAPIView
from ..decorators import except_connection_errors
from ..permissions import DevicePermission
from ..serializers import (
    InterfacesCommentsSerializer,
    ADSLProfileSerializer,
    PortControlSerializer,
    PoEPortStatusSerializer,
)
from ..swagger import schemas


@method_decorator(schemas.port_control_api_doc, name="post")  # API DOC
@method_decorator(profile_permission(models.Profile.REBOOT), name="dispatch")
class InterfaceControlAPIView(UserAuthenticatedAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]
    serializer_class = PortControlSerializer

    @except_connection_errors
    def post(self, request: Request, device_name: str):
        """
        ## Изменяем состояние порта оборудования
        """

        # Проверяем данные, полученные в запросе, с помощью сериализатора.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        port_status: str = serializer.validated_data["status"]
        port_name: str = serializer.validated_data["port"]
        save_config: bool = serializer.validated_data["save"]

        device = get_object_or_404(models.Devices, name=device_name)

        # Есть ли у пользователя доступ к группе данного оборудования.
        self.check_object_permissions(request, device)

        # Есть ли у пользователя доступ к порту данного оборудования.
        interface = check_user_interface_permission(self.current_user, device, port_name, action=port_status)

        change_status = change_port_state(
            device, port_name=port_name, port_status=port_status, save_config=save_config
        )

        # Логи
        log(self.current_user, device, f"{port_status} port {port_name} ({interface.desc}) \n{change_status}")

        return Response(serializer.validated_data, status=200)


@method_decorator(profile_permission(models.Profile.BRAS), name="dispatch")
class ChangeDescriptionAPIView(UserAuthenticatedAPIView):
    """
    ## Изменяем описание на порту у оборудования
    """

    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    def post(self, request: Request, device_name: str):
        """
        ## Меняем описание на порту оборудования

        Требуется передать JSON:

            {
                "port": "порт оборудования",
                "description": "новое описание порта"
            }

        Если указанного порта не существует на оборудовании, то будет отправлен ответ со статусом `400`

            {
                "detail": "Неверный порт {port}"
            }

        Если описание слишком длинное, то будет отправлен ответ со статусом `400`

            {
                "detail": "Слишком длинное описание! Укажите не более {max_length} символов."
            }

        """

        port = self.request.data.get("port", "")
        new_description = self.request.data.get("description", "")
        if not port:
            raise ValidationError({"detail": "Необходимо указать порт"})

        device = get_object_or_404(models.Devices, name=device_name)

        # Проверяем права доступа пользователя к оборудованию
        self.check_object_permissions(request, device)
        # Проверяем права доступа пользователя к порту.
        check_user_interface_permission(self.current_user, device, port)

        description_status = set_interface_description(
            device, interface_name=port, description=new_description
        )

        log(self.current_user, device, str(description_status))

        return Response(
            {
                "description": description_status.description,
                "port": description_status.port,
                "saved": description_status.saved,
            }
        )


class MacListAPIView(UserAuthenticatedAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    def get(self, request: Request, device_name):
        """
        ## Смотрим MAC-адреса на порту оборудования

        Для этого необходимо передать порт в параметре URL `?port=eth1`

        Если порт верный и там есть MAC-адреса, то будет вот такой ответ:

            {
                "count": 47,
                "result": [
                    {
                        "vlanID": "1051",
                        "mac": "00-04-96-51-AD-3D",
                        "vlanName": "Описание VLAN"
                    },
                    ...
                ]
            }

        """

        port: str = self.request.GET.get("port", "")
        if not port:
            raise ValidationError({"detail": "Укажите порт!"})

        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        macs = get_mac_addresses_on_interface(device, port)

        return Response({"count": len(macs), "result": macs})


class CableDiagAPIView(UserAuthenticatedAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    def get(self, request: Request, device_name):
        """
        ## Запускаем диагностику кабеля на порту

        Для этого необходимо передать порт в параметре URL `?port=eth1`

        Функция возвращает данные в виде словаря.
        В зависимости от результата диагностики некоторые ключи могут отсутствовать за ненадобностью.

            {
                "len": "-",         # Длина кабеля в метрах, либо "-", когда не определено
                "status": "",       # Состояние на порту (Up, Down, Empty)
                "pair1": {
                    "status": "",   # Статус первой пары (Open, Short)
                    "len": "",      # Длина первой пары в метрах
                },
                "pair2": {
                    "status": "",   # Статус второй пары (Open, Short)
                    "len": "",      # Длина второй пары в метрах
                }
            }

        """

        if not request.GET.get("port"):
            raise ValidationError({"detail": "Неверные данные"})

        # Находим оборудование
        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        # Если оборудование недоступно
        if not device.available:
            return Response({"detail": "Device unavailable"}, status=500)

        try:
            cable_test = device.connect().virtual_cable_test(request.GET["port"])
        except InvalidMethod:
            return Response({"detail": "Unsupported for this device"}, status=400)
        else:
            return Response(cable_test)


@method_decorator(profile_permission(models.Profile.BRAS), name="dispatch")
class SetPoEAPIView(UserAuthenticatedAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]
    serializer_class = PoEPortStatusSerializer

    @except_connection_errors
    def post(self, request: Request, device_name):
        """
        ## Устанавливает PoE статус на порту
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        poe_status = serializer.validated_data["status"]
        port_name = serializer.validated_data["port"]

        # Находим оборудование
        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        # Если оборудование недоступно
        if not device.available:
            return Response({"detail": "Device unavailable"}, status=500)

        try:
            _, err = device.connect().set_poe_out(port_name, poe_status)
        except InvalidMethod:
            return Response({"detail": "Unsupported for this device"}, status=400)
        else:
            if not err:
                return Response({"status": poe_status})
            return Response({"detail": f"Invalid data ({poe_status})"}, status=400)


class InterfaceInfoAPIView(UserAuthenticatedAPIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    def get(self, request: Request, device_name):
        """
        ## Общая информация об определенном порте оборудования

        В зависимости от типа оборудования информация будет совершенно разной

        Поле `portDetailInfo.type` указывает тип данных, которые могут быть строкой, JSON, или HTML кодом.

            {
                "portDetailInfo": {
                    "type": "text",  - Тип данных для детальной информации о порте
                    "data": ""       - Сами данные
                },
                "portConfig":   "Конфигурация порта (из файла конфигурации)",
                "portType":     "COPPER"    - (SFP, COMBO),
                "portErrors":   "Ошибки на порту",
                "hasCableDiag": true        - Имеется ли на данном типе оборудования возможность диагностики порта
            }

        """

        port = self.request.GET.get("port")
        if not port:
            raise ValidationError({"detail": "Укажите порт!"})

        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        result = get_interface_detail_info(device, port)  # Получаем информацию о порте

        return Response(result)


@method_decorator(profile_permission(models.Profile.BRAS), name="dispatch")
class ChangeDSLProfileAPIView(APIView):
    permission_classes = [IsAuthenticated, DevicePermission]

    @except_connection_errors
    def post(self, request, device_name: str):
        """
        ## Изменяем профиль xDSL порта на другой

        Возвращаем `{ "status": status }` или `{ "error": error }`

        """

        serializer = ADSLProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device = get_object_or_404(models.Devices, name=device_name)
        self.check_object_permissions(request, device)

        # Если оборудование недоступно
        if not device.available:
            return Response({"detail": "Device unavailable"}, status=500)

        # Подключаемся к оборудованию
        session = device.connect()
        try:
            status = session.change_profile(
                serializer.validated_data["port"],
                serializer.validated_data["index"],
            )
        except InvalidMethod:
            # Нельзя менять профиль для данного устройства
            return Response({"error": "Device can't change profile"}, status=400)
        else:
            return Response({"status": status})


class CreateInterfaceCommentAPIView(generics.CreateAPIView):
    serializer_class = InterfacesCommentsSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InterfaceCommentAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.InterfacesComments.objects.all()
    serializer_class = InterfacesCommentsSerializer
    lookup_field = "pk"
    lookup_url_kwarg = "pk"
