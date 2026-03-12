## crm_service\apps\interactions\models.py
from django.db import models


class Interaction(models.Model):

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        PHONE = "phone", "Phone"
        WHATSAPP = "whatsapp", "WhatsApp"
        CHAT = "chat", "Chat (Chatbot)"
        MEETING = "meeting", "Meeting"
        OTHER = "other", "Other"

    class Direction(models.TextChoices):
        INBOUND = "inbound", "Inbound"
        OUTBOUND = "outbound", "Outbound"

    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.CASCADE,
        related_name="interactions",
    )
    agent = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="interactions",
        help_text="El agente que manejó esta interacción (null = bot).",
    )
    channel = models.CharField(max_length=20, choices=Channel.choices)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    external_id = models.CharField(max_length=255, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["contact", "occurred_at"]),
            models.Index(fields=["channel"]),
        ]

    def __str__(self):
        return f"[{self.channel}] {self.contact} @ {self.occurred_at:%Y-%m-%d %H:%M}"
