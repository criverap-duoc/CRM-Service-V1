## crm_service\crm_service\urls.py
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/v1/", include([
        path("auth/", include("apps.contacts.urls.auth")),
        path("contacts/", include("apps.contacts.urls.contacts")),
        path("interactions/", include("apps.interactions.urls")),
        path("integrations/", include("apps.integrations.urls")),
    ])),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
