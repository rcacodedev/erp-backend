from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EventViewSet, NoteViewSet, AlertsViewSet, OverlaysViewSet

router = DefaultRouter()
router.register(r"events", EventViewSet, basename="agenda-events")
router.register(r"notes", NoteViewSet, basename="agenda-notes")
router.register(r"alerts", AlertsViewSet, basename="agenda-alerts")
router.register(r"overlays", OverlaysViewSet, basename="agenda-overlays")

urlpatterns = [ path("", include(router.urls)), ]
