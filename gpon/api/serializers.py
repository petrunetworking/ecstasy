import re
from typing import Optional

import orjson
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator, MaxValueValidator
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from check.models import Devices
from ..models import Address, OLTState, HouseOLTState


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"

    @staticmethod
    def validate_region(value: str):
        if len(value) < 5:
            raise ValidationError("Регион должен содержать более 4 символов")
        return value.capitalize()

    @staticmethod
    def validate_planStructure(value: str):
        if not value:  # Это не обязательное поле
            return value

        if len(value) < 5:  # Но если указано, то должно быть более 4
            raise ValidationError("Регион должен содержать более 4 символов")

        return value.capitalize()

    @staticmethod
    def validate_street(value: str):
        if not value:  # Это не обязательное поле
            return value

        # Но если указано, то проверяем правильность
        if not re.search(r"улица|проспект|проезд|бульвар|шоссе|переулок|тупик", value):
            raise ValidationError(
                "Укажите полное название с указанием типа"
                " (улица/проспект/проезд/бульвар/шоссе/переулок/тупик)"
            )

        if len(value) < 10:
            raise ValidationError("Название улицы должно быть длиннее :)")

        return value.capitalize()

    @staticmethod
    def validate_settlement(value: str):
        if len(value) < 5:
            raise ValidationError("Регион должен содержать более 4 символов")
        return value.capitalize()

    @staticmethod
    def validate(data):
        if not data["planStructure"] and not data["street"]:
            raise ValidationError("Необходимо указать либо СНТ ТСН, либо Улицу")


class OLTStateSerializer(serializers.ModelSerializer):
    deviceName = serializers.CharField(source="device.name")
    devicePort = serializers.CharField(source="olt_port")

    class Meta:
        model = OLTState
        fields = ["deviceName", "devicePort", "fiber", "description"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._device: Optional[Devices] = None

    def validate_deviceName(self, value):
        try:
            self._device: Devices = Devices.objects.get(name=value)
        except Devices.DoesNotExist:
            raise ValidationError(f"Оборудование `{value}` не существует")
        return value

    def validate_devicePort(self, value):
        if self._device is None:
            return value
        try:
            interfaces = orjson.loads(self._device.devicesinfo.interfaces or "[]")
        except ObjectDoesNotExist:
            raise ValidationError(
                "Данное оборудование не имеет портов для проверки, "
                "пожалуйста, откройте его, чтобы опросить"
            )
        else:
            for intf in interfaces:
                if intf["Interface"] == value:
                    return value

        raise ValidationError(f"Данное оборудование не имеет порта `{value}`")

    def create(self, validated_data) -> OLTState:
        if self._device is None:
            self._device: Devices = Devices.objects.get(name=validated_data["device"]["name"])

        instance = OLTState.objects.create(
            device=self._device,
            olt_port=validated_data["olt_port"],
            fiber=validated_data.get("fiber"),
            description=validated_data.get("description"),
        )

        return instance


class HouseBAddressSerializer(AddressSerializer):
    building_type = serializers.ChoiceField(
        choices=["building", "house"], required=True, write_only=True
    )
    floors = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)], required=True, write_only=True
    )
    total_entrances = serializers.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(255)], required=True, write_only=True
    )

    class Meta:
        model = Address
        fields = [
            "id",
            "region",
            "settlement",
            "planStructure",
            "street",
            "house",
            "block",
            "building_type",
            "floors",
            "total_entrances",
        ]


class HouseOLTStateSerializer(serializers.ModelSerializer):
    address = AddressSerializer(source="house.address")

    class Meta:
        model = HouseOLTState
        fields = ["entrances", "description"]

    def create(self, validated_data):
        building_type = validated_data["address"]["building_type"]

    def to_representation(self, instance: HouseOLTState):
        data = super().to_representation(instance)
        data["houseB"]["address"]["building_type"] = (
            "building" if instance.house.apartment_building else "house"
        )
        data["houseB"]["address"]["total_entrances"] = instance.house.total_entrances
        data["houseB"]["address"]["floors"] = instance.house.floors

        return data


class CreateTechDataSerializer(serializers.Serializer):
    oltState = OLTStateSerializer()
    houseB = HouseOLTStateSerializer()

    class Meta:
        fields = ["oltState", "houseB"]

    def validate(self, data):
        pass

    def validate_oltState(self):
        pass

    def create(self, validated_data):
        pass
