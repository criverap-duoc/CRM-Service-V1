## crm_service\tests\test_contacts.py
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from apps.contacts.models import Contact


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(username="agent", password="pass1234", email="agent@test.com")


@pytest.fixture
def auth_client(api_client, user):
    response = api_client.post(
        "/api/v1/auth/token/",
        {"username": "agent", "password": "pass1234"},
        format="json",
    )
    token = response.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


@pytest.fixture
def contact(db, user):
    return Contact.objects.create(
        first_name="Ana",
        last_name="Pérez",
        email="ana@example.com",
        status=Contact.Status.LEAD,
        source=Contact.Source.ORGANIC,
        assigned_to=user,
    )


@pytest.mark.django_db
class TestAuth:
    def test_obtain_token(self, api_client, user):
        res = api_client.post(
            "/api/v1/auth/token/",
            {"username": "agent", "password": "pass1234"},
            format="json",
        )
        assert res.status_code == 200
        assert "access" in res.data
        assert "refresh" in res.data

    def test_unauthenticated_request_returns_401(self, api_client):
        res = api_client.get("/api/v1/contacts/")
        assert res.status_code == 401


@pytest.mark.django_db
class TestContactsCRUD:
    def test_list_contacts(self, auth_client, contact):
        res = auth_client.get("/api/v1/contacts/")
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_create_contact(self, auth_client, user):
        payload = {
            "first_name": "Carlos",
            "last_name": "González",
            "email": "carlos@example.com",
            "source": "referral",
        }
        res = auth_client.post("/api/v1/contacts/", payload, format="json")
        assert res.status_code == 201
        assert res.data["email"] == "carlos@example.com"

    def test_create_contact_duplicate_email_returns_400(self, auth_client, contact):
        payload = {
            "first_name": "Otra",
            "last_name": "Persona",
            "email": contact.email,
        }
        res = auth_client.post("/api/v1/contacts/", payload, format="json")
        assert res.status_code == 400

    def test_retrieve_contact(self, auth_client, contact):
        res = auth_client.get(f"/api/v1/contacts/{contact.pk}/")
        assert res.status_code == 200
        assert res.data["email"] == contact.email

    def test_partial_update(self, auth_client, contact):
        res = auth_client.patch(
            f"/api/v1/contacts/{contact.pk}/",
            {"company": "ACME Corp"},
            format="json",
        )
        assert res.status_code == 200
        assert res.data["company"] == "ACME Corp"

    def test_delete_contact(self, auth_client, contact):
        res = auth_client.delete(f"/api/v1/contacts/{contact.pk}/")
        assert res.status_code == 204
        assert not Contact.objects.filter(pk=contact.pk).exists()


@pytest.mark.django_db
class TestContactActions:
    def test_change_status(self, auth_client, contact):
        res = auth_client.patch(
            f"/api/v1/contacts/{contact.pk}/status/",
            {"status": "customer"},
            format="json",
        )
        assert res.status_code == 200
        contact.refresh_from_db()
        assert contact.status == Contact.Status.CUSTOMER

    def test_change_status_invalid(self, auth_client, contact):
        res = auth_client.patch(
            f"/api/v1/contacts/{contact.pk}/status/",
            {"status": "flying_unicorn"},
            format="json",
        )
        assert res.status_code == 400

    def test_mine_endpoint(self, auth_client, contact):
        res = auth_client.get("/api/v1/contacts/mine/")
        assert res.status_code == 200
        emails = [c["email"] for c in res.data["results"]]
        assert contact.email in emails


@pytest.mark.django_db
class TestContactFiltering:
    def test_filter_by_status(self, auth_client, contact):
        res = auth_client.get("/api/v1/contacts/?status=lead")
        assert res.status_code == 200
        assert res.data["count"] == 1

    def test_search_by_email(self, auth_client, contact):
        res = auth_client.get("/api/v1/contacts/?search=ana@example")
        assert res.status_code == 200
        assert res.data["count"] == 1
