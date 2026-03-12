## crm_service\apps\integrations\urls.py
from django.urls import path
from .views import MetaWebhookView, SummarizeInteractionView

urlpatterns = [
    path("meta/webhook/", MetaWebhookView.as_view(), name="meta-webhook"),
    path("ai/summarize/", SummarizeInteractionView.as_view(), name="ai-summarize"),
]
