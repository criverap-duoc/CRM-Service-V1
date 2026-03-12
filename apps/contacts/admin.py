## crm_service\apps\contacts\admin.py
from django.contrib import admin
from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ["full_name", "email", "company", "status", "source", "assigned_to", "created_at"]
    list_filter = ["status", "source", "assigned_to"]
    search_fields = ["first_name", "last_name", "email", "company"]
    raw_id_fields = ["assigned_to"]
    date_hierarchy = "created_at"
