from django.urls import path

from .views import SeekInkSettings

urlpatterns = [
    path(
        "control/event/<str:organizer>/<str:event>/seekink/",
        SeekInkSettings.as_view(),
        name="settings",
    ),
]
