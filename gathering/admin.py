from django.contrib import admin
from .models import MacAddress
from .paginator import LargeTablePaginator


@admin.register(MacAddress)
class MacAddressesAdmin(admin.ModelAdmin):
    list_display = ["address", "vlan", "device", "port", "datetime"]
    list_select_related = ["device"]
    paginator = LargeTablePaginator
