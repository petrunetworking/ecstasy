"""
URL Configuration для API
Расширенное от /device/api/
"""

from django.urls import path
from .views import devices_info, device_manager

# /device/api/

urlpatterns = [
    path("workload/interfaces", devices_info.AllDevicesInterfacesWorkLoadAPIView.as_view()),
    path(
        "workload/interfaces/<device_name>",
        devices_info.DeviceInterfacesWorkLoadAPIView.as_view(),
    ),
    path("list_all", devices_info.DevicesListAPIView.as_view()),

    path("<device_name>/change-description", device_manager.ChangeDescription.as_view()),
    path("<device_name>/interfaces", devices_info.DeviceInterfacesAPIView.as_view()),
    path("<device_name>/info", devices_info.DeviceInfoAPIView.as_view()),
    path("<device_name>/stats", devices_info.DeviceStatsInfoAPIView.as_view()),
    path("comments", device_manager.CreateInterfaceCommentAPIView.as_view()),
    path("comments/<int:pk>", device_manager.InterfaceCommentAPIView.as_view()),
]
