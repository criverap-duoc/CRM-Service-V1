## crm_service\tests\test_interactions.py
import pytest
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from apps.contacts.models import Contact
from apps.interactions.models import Interaction


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
    def test_webhook_creates_contact(self, api_client):
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

    def test_webhook_idempotent(self, api_client):
        payload = {"email": "idempotent@meta.com", "first_name": "Test", "last_name": "User"}
        api_client.post("/api/v1/integrations/meta/webhook/", payload, format="json")
        api_client.post("/api/v1/integrations/meta/webhook/", payload, format="json")
        assert Contact.objects.filter(email="idempotent@meta.com").count() == 1

@pytest.mark.django_db
class TestHealthCheck:
    def test_health_ok(self, api_client):
        res = api_client.get("/health/")
        assert res.status_code == 200
        assert res.data["status"] == "ok"
        assert res.data["database"] == "ok"
