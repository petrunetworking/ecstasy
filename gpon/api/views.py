import orjson
from django.core.cache import cache
from django.db.models import QuerySet
from django.db.transaction import atomic
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response

from check.models import Devices
from .serializers.address import AddressSerializer, BuildingAddressSerializer
from .serializers.common import End3Serializer
from .serializers.create_tech_data import CreateTechDataSerializer, OLTStateSerializer
from .serializers.view_tech_data import ViewOLTStatesTechDataSerializer, TechCapabilitySerializer
from ..models import End3, HouseB, HouseOLTState, OLTState


class TechDataListCreateAPIView(GenericAPIView):
    """
    Предназначен для создания и просмотра технических данных
    """

    cache_key = "gpon:api:TechDataListCreateAPIView:get"
    cache_timeout = 60 * 2

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateTechDataSerializer

    def get(self, request) -> Response:
        data = cache.get(self.cache_key, [])
        if data:
            return Response(data)

        buildings = HouseB.objects.all().select_related("address")

        for house in buildings:
            house: HouseB
            for house_olt_state in (
                house.house_olt_states.all()
                .select_related("statement", "statement__device")
                .prefetch_related("end3_set")
            ):
                house_olt_state: HouseOLTState
                end3: End3 = house_olt_state.end3_set.first()
                data.append(
                    {
                        **OLTStateSerializer(instance=house_olt_state.statement).data,
                        "address": AddressSerializer(instance=house.address).data,
                        "entrances": house_olt_state.entrances,
                        "customerLine": {
                            "type": end3.type,
                            "count": house_olt_state.end3_set.count(),
                            "typeCount": end3.capacity,
                        },
                    }
                )

        cache.set(self.cache_key, data, timeout=self.cache_timeout)

        return Response(data)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with atomic():
            serializer.create(serializer.validated_data)
        return Response(serializer.data, status=201)


class ViewOLTStateTechData(GenericAPIView):
    serializer_class = ViewOLTStatesTechDataSerializer

    def get_object(self):
        device_name = self.kwargs["device_name"]
        olt_port = self.request.GET.get("port")

        try:
            return OLTState.objects.select_related("device").get(
                device__name=device_name, olt_port=olt_port
            )
        except OLTState.DoesNotExist:
            raise ValidationError(
                f"Не удалось найти OLT подключение оборудования {device_name} на порту {olt_port}"
            )

    def get(self, request, *args, **kwargs):
        olt_state = self.get_object()
        serializer = self.get_serializer(instance=olt_state)
        return Response(serializer.data)


class BuildingsAddressesListAPIView(ListAPIView):
    serializer_class = BuildingAddressSerializer
    queryset = HouseB.objects.all().select_related("address")


class SplitterAddressesListAPIView(ListAPIView):
    serializer_class = End3Serializer
    queryset = End3.objects.select_related("address").filter(type="splitter")

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        port = self.request.GET.get("port")
        device = self.request.GET.get("device")
        if not port and not device:
            return queryset

        try:
            olt_state: OLTState = OLTState.objects.get(olt_port=port, device__name=device)
        except OLTState.DoesNotExist:
            return queryset.none()
        addresses_ids = set()
        for house_olt_state in olt_state.house_olt_states.all():
            house_olt_state: HouseOLTState
            addresses_ids |= set(
                house_olt_state.end3_set.all()
                .select_related("address")
                .values_list("address", flat=True)
            )

        return queryset.filter(address_id__in=addresses_ids)


class DevicesNamesListAPIView(GenericAPIView):
    def get_queryset(self):
        """
        ## Возвращаем queryset всех устройств из доступных для пользователя групп
        """

        # Фильтруем запрос
        group_ids = self.request.user.profile.devices_groups.all().values_list("id", flat=True)
        return Devices.objects.filter(group_id__in=group_ids).select_related("group")

    def get(self, request, *args, **kwargs) -> Response:
        device_names = self.get_queryset().values_list("name", flat=True)
        return Response(device_names)


class DevicePortsList(DevicesNamesListAPIView):
    def get(self, request, *args, **kwargs) -> Response:
        try:
            device: Devices = self.get_queryset().get(name=self.kwargs["device_name"])
        except Devices.DoesNotExist:
            return Response({"error": "Оборудование не существует"}, status=400)

        interfaces = orjson.loads(device.devicesinfo.interfaces or "[]")

        interfaces_names = list(map(lambda x: x["Interface"], interfaces))
        return Response(interfaces_names)


class End3TechCapabilitySerializer(GenericAPIView):
    queryset = End3.objects.all()
    serializer_class = TechCapabilitySerializer

    def get(self, request, *args, **kwargs):
        end3: End3 = self.get_object()
        # end3.techcapability_set.get().subscriber_connection.get()
        serializer = self.get_serializer(instance=end3.techcapability_set, many=True)
        return Response(serializer.data)
