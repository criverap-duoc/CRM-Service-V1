## crm_service\apps\integrations\serializers.py
from rest_framework import serializers


class MetaLeadWebhookSerializer(serializers.Serializer):
    lead_id = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField()
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)


class SummarizeInteractionSerializer(serializers.Serializer):
    interaction_id = serializers.IntegerField()


class SummarizeResponseSerializer(serializers.Serializer):
    interaction_id = serializers.IntegerField()
    summary = serializers.CharField()
