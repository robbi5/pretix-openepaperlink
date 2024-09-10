from django.urls import path

from .views import OpenEPaperLinkSettings

urlpatterns = [
    path(
        "control/event/<str:organizer>/<str:event>/openepaperlink/",
        OpenEPaperLinkSettings.as_view(),
        name="settings",
    ),
]
