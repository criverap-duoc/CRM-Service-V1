## crm_service\apps\interactions\serializers.py
from rest_framework import serializers
from .models import Interaction


class InteractionSerializer(serializers.ModelSerializer):
    agent_username = serializers.CharField(source="agent.username", read_only=True, allow_null=True)

    class Meta:
        model = Interaction
        fields = [
            "id",
            "contact",
            "agent",
            "agent_username",
            "channel",
            "direction",
            "subject",
            "body",
            "external_id",
            "metadata",
            "occurred_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "agent_username"]

    def validate(self, attrs):
        from django.utils import timezone
        occurred_at = attrs.get("occurred_at")
        if occurred_at and occurred_at > timezone.now():
            raise serializers.ValidationError(
                {"occurred_at": "Interaction date cannot be in the future."}
            )
        return attrs


class InteractionListSerializer(serializers.ModelSerializer):
    agent_username = serializers.CharField(source="agent.username", read_only=True, allow_null=True)

    class Meta:
        model = Interaction
        fields = ["id", "contact", "channel", "direction", "subject", "agent_username", "occurred_at"]
