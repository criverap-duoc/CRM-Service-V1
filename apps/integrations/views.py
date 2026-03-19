import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework import status
from drf_spectacular.utils import extend_schema

from apps.contacts.models import Contact
from apps.interactions.models import Interaction
from .clients import MetaClient, OpenAIClient
from .serializers import (
    MetaLeadWebhookSerializer,
    SummarizeInteractionSerializer,
    SummarizeResponseSerializer,
)

logger = logging.getLogger(__name__)


class WebhookRateThrottle(AnonRateThrottle):
    scope = "webhook"


class MetaWebhookView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [WebhookRateThrottle]

    @extend_schema(
        summary="Meta Lead Ads webhook",
        request=MetaLeadWebhookSerializer,
        responses={200: {"type": "object", "properties": {"received": {"type": "boolean"}}}},
        tags=["Integrations"],
    )
    def post(self, request):
        serializer = MetaLeadWebhookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        email = payload["email"]
        contact, created = Contact.objects.get_or_create(
            email=email,
            defaults={
                "first_name": payload.get("first_name", ""),
                "last_name": payload.get("last_name", ""),
                "phone": payload.get("phone", ""),
                "source": Contact.Source.META_ADS,
                "status": Contact.Status.LEAD,
            },
        )

        Interaction.objects.create(
            contact=contact,
            channel=Interaction.Channel.OTHER,
            direction=Interaction.Direction.INBOUND,
            subject="Meta Lead Ad submission",
            external_id=payload.get("lead_id", ""),
            metadata=payload,
            occurred_at=timezone.now(),
        )

        logger.info("Meta webhook: contact %s (%s)", contact.pk, "created" if created else "exists")
        return Response({"received": True}, status=status.HTTP_200_OK)


class SummarizeInteractionView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="AI summary of an interaction",
        request=SummarizeInteractionSerializer,
        responses={200: SummarizeResponseSerializer},
        tags=["Integrations"],
    )
    def post(self, request):
        serializer = SummarizeInteractionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interaction_id = serializer.validated_data["interaction_id"]

        try:
            interaction = Interaction.objects.get(pk=interaction_id)
        except Interaction.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": f"Interaction {interaction_id} not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        client = OpenAIClient()
        try:
            summary = client.summarize_interaction(interaction.body or interaction.subject)
        except Exception as exc:
            logger.error("OpenAI summarize failed: %s", exc)
            return Response(
                {"error": {"code": "integration_error", "message": "Could not reach OpenAI."}},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"interaction_id": interaction.pk, "summary": summary})
