## crm_service\tests\test_interactions.py
import pytest
import hmac
import hashlib
import json

from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from apps.contacts.models import Contact
from apps.interactions.models import Interaction
from unittest.mock import patch, MagicMock

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="agent2", password="pass1234")


@pytest.fixture
def auth_client(api_client, user):
    res = api_client.post(
        "/api/v1/auth/token/",
        {"username": "agent2", "password": "pass1234"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
    return api_client


@pytest.fixture
def contact(db, user):
    return Contact.objects.create(
        first_name="Luis",
        last_name="Torres",
        email="luis@example.com",
        assigned_to=user,
    )


@pytest.fixture
def interaction(db, contact, user):
    return Interaction.objects.create(
        contact=contact,
        agent=user,
        channel=Interaction.Channel.EMAIL,
        direction=Interaction.Direction.INBOUND,
        subject="Hello from customer",
        body="I need help with my order.",
        occurred_at=timezone.now(),
    )


@pytest.mark.django_db
class TestInteractions:
    def test_create_interaction(self, auth_client, contact):
        payload = {
            "contact": contact.pk,
            "channel": "email",
            "direction": "inbound",
            "subject": "Initial inquiry",
            "body": "Hi, I'm interested in your product.",
            "occurred_at": timezone.now().isoformat(),
        }
        res = auth_client.post("/api/v1/interactions/", payload, format="json")
        assert res.status_code == 201
        assert res.data["subject"] == "Initial inquiry"

    def test_list_interactions_filter_by_contact(self, auth_client, interaction, contact):
        res = auth_client.get(f"/api/v1/interactions/?contact={contact.pk}")
        assert res.status_code == 200
        assert res.data["count"] >= 1

    def test_future_occurred_at_returns_400(self, auth_client, contact):
        from datetime import timedelta
        future = (timezone.now() + timedelta(days=1)).isoformat()
        payload = {
            "contact": contact.pk,
            "channel": "phone",
            "direction": "outbound",
            "subject": "Follow up",
            "occurred_at": future,
        }
        res = auth_client.post("/api/v1/interactions/", payload, format="json")
        assert res.status_code == 400


@pytest.mark.django_db
class TestMetaWebhook:
    def test_webhook_creates_contact(self, api_client, settings):
        settings.META_APP_SECRET = ""
        payload = {
            "lead_id": "meta_lead_001",
            "email": "lead@meta.com",
            "first_name": "Meta",
            "last_name": "Lead",
            "phone": "+56912345678",
        }
        res = api_client.post("/api/v1/integrations/meta/webhook/", payload, format="json")
        assert res.status_code == 200
        assert res.data["received"] is True
        assert Contact.objects.filter(email="lead@meta.com").exists()

    def test_webhook_idempotent(self, api_client, settings):
        settings.META_APP_SECRET = ""
        payload = {"email": "idempotent@meta.com", "first_name": "Test", "last_name": "User"}
        api_client.post("/api/v1/integrations/meta/webhook/", payload, format="json")
        api_client.post("/api/v1/integrations/meta/webhook/", payload, format="json")
        assert Contact.objects.filter(email="idempotent@meta.com").count() == 1


@pytest.mark.django_db
class TestRateLimiting:
    def test_webhook_acepta_requests_normales(self, api_client, settings):
        settings.META_APP_SECRET = ""
        payload = {"email": "rate@test.com", "first_name": "Rate", "last_name": "Test"}
        res = api_client.post("/api/v1/integrations/meta/webhook/", payload, format="json")
        assert res.status_code == 200

    def test_auth_endpoint_no_requiere_token(self, api_client):
        res = api_client.post(
            "/api/v1/auth/token/",
            {"username": "noexiste", "password": "mal"},
            format="json",
        )
        assert res.status_code == 401


@pytest.mark.django_db
class TestMetaWebhookFirma:
    def _firma(self, payload: dict, secret: str) -> str:
        """Helper que genera la firma correcta para un payload."""
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        return "sha256=" + hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()

    def test_webhook_sin_firma_pasa_si_no_hay_secret(self, api_client, settings):
        """Sin META_APP_SECRET configurado, el webhook acepta cualquier request."""
        settings.META_APP_SECRET = ""
        payload = {"email": "nofirma@test.com", "first_name": "Sin", "last_name": "Firma"}
        res = api_client.post(
            "/api/v1/integrations/meta/webhook/",
            payload,
            format="json",
        )
        assert res.status_code == 200

    def test_webhook_firma_invalida_retorna_403(self, api_client, settings):
        """Con META_APP_SECRET configurado, firma incorrecta retorna 403."""
        settings.META_APP_SECRET = "mi-secret-de-prueba"
        payload = {"email": "firmamala@test.com", "first_name": "Firma", "last_name": "Mala"}
        res = api_client.post(
            "/api/v1/integrations/meta/webhook/",
            payload,
            format="json",
            HTTP_X_HUB_SIGNATURE_256="sha256=firmainvalida",
        )
        assert res.status_code == 403

    def test_webhook_sin_header_firma_retorna_403(self, api_client, settings):
        """Con META_APP_SECRET configurado, request sin header retorna 403."""
        settings.META_APP_SECRET = "mi-secret-de-prueba"
        payload = {"email": "sinfirma@test.com", "first_name": "Sin", "last_name": "Header"}
        res = api_client.post(
            "/api/v1/integrations/meta/webhook/",
            payload,
            format="json",
        )
        assert res.status_code == 403


@pytest.mark.django_db
class TestSummarizeInteraction:
    def test_summarize_interaction_no_existe_retorna_404(self, auth_client):
        res = auth_client.post(
            "/api/v1/integrations/ai/summarize/",
            {"interaction_id": 99999},
            format="json",
        )
        assert res.status_code == 404
        assert res.data["error"]["code"] == "not_found"

    def test_summarize_interaction_ok(self, auth_client, interaction):
        with patch("apps.integrations.views.OpenAIClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.summarize_interaction.return_value = "Resumen de prueba."
            MockClient.return_value = mock_instance

            res = auth_client.post(
                "/api/v1/integrations/ai/summarize/",
                {"interaction_id": interaction.pk},
                format="json",
            )

        assert res.status_code == 200
        assert res.data["summary"] == "Resumen de prueba."

    def test_summarize_interaction_error_openai_retorna_502(self, auth_client, interaction):
        with patch("apps.integrations.views.OpenAIClient") as MockClient:
            mock_instance = MagicMock()
            mock_instance.summarize_interaction.side_effect = Exception("OpenAI caído")
            MockClient.return_value = mock_instance

            res = auth_client.post(
                "/api/v1/integrations/ai/summarize/",
                {"interaction_id": interaction.pk},
                format="json",
            )

        assert res.status_code == 502
        assert res.data["error"]["code"] == "integration_error"


@pytest.mark.django_db
class TestHealthCheckDB:
    def test_health_db_caida_retorna_503(self, api_client):
        from django.db import connection
        with patch.object(connection, "ensure_connection", side_effect=Exception("DB caída")):
            res = api_client.get("/health/")
        assert res.status_code == 503
        assert res.data["status"] == "degraded"
        assert res.data["database"] == "unavailable"


@pytest.mark.django_db
class TestMetaWebhookFirmaValida:
    def test_webhook_firma_valida_retorna_200(self, api_client, settings):
        import json
        secret = "mi-secret-de-prueba"
        settings.META_APP_SECRET = secret

        payload = {"email": "firmaok@test.com", "first_name": "Firma", "last_name": "OK"}

        # Generar firma correcta
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        firma = "sha256=" + hmac.new(
            secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()

        res = api_client.post(
            "/api/v1/integrations/meta/webhook/",
            data=body,
            content_type="application/json",
            HTTP_X_HUB_SIGNATURE_256=firma,
        )
        assert res.status_code == 200
        assert Contact.objects.filter(email="firmaok@test.com").exists()
