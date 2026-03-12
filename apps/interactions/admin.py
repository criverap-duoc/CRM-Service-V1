## crm_service\apps\interactions\admin.py
from django.contrib import admin
from .models import Interaction


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ["contact", "channel", "direction", "subject", "agent", "occurred_at"]
    list_filter = ["channel", "direction"]
    search_fields = ["subject", "body", "external_id", "contact__email"]
    date_hierarchy = "occurred_at"
    raw_id_fields = ["contact", "agent"]
