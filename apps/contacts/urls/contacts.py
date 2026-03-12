## crm_service\apps\contacts\urls\contacts.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.contacts.views import ContactViewSet

router = DefaultRouter()
router.register(r"", ContactViewSet, basename="contact")

urlpatterns = [
    path("", include(router.urls)),
]
