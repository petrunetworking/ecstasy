from django.urls import path

from . import views

# /gpon/api/

app_name = "api"

urlpatterns = [
    path("tech-data", views.TechDataListCreateAPIView.as_view(), name="tech-data"),
    path("tech-data/<device_name>", views.ViewOLTStateTechData.as_view(), name="view-olt-state-tech-data"),
    path("tech-data/olt-state/<int:pk>", views.PatchOLTStateAPIView.as_view(), name="tech-data-olt-state"),
    path("tech-capability/<int:pk>", views.End3TechCapabilitySerializer.as_view(), name="tech-capability-end3"),
    path("devices-names", views.DevicesNamesListAPIView.as_view(), name="devices-names"),
    path("ports-names/<str:device_name>", views.DevicePortsList.as_view(), name="ports-names"),
    path(
        "addresses/buildings",
        views.BuildingsAddressesListAPIView.as_view(),
        name="building-addresses",
    ),
    path(
        "addresses/splitters",
        views.SplitterAddressesListAPIView.as_view(),
        name="splitter-addresses",
    ),
]
