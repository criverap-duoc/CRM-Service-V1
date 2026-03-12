## crm_service\apps\contacts\views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Contact
from .serializers import ContactSerializer, ContactListSerializer
from .filters import ContactFilter
from .permissions import IsManager, IsAgentOrManager


@extend_schema_view(
    list=extend_schema(summary="List contacts", tags=["Contacts"]),
    create=extend_schema(summary="Create contact", tags=["Contacts"]),
    retrieve=extend_schema(summary="Get contact", tags=["Contacts"]),
    update=extend_schema(summary="Update contact", tags=["Contacts"]),
    partial_update=extend_schema(summary="Partial update contact", tags=["Contacts"]),
    destroy=extend_schema(summary="Delete contact", tags=["Contacts"]),
)
class ContactViewSet(viewsets.ModelViewSet):
    filterset_class = ContactFilter
    search_fields = ["first_name", "last_name", "email", "company"]
    ordering_fields = ["created_at", "updated_at", "last_name", "status"]
    ordering = ["-created_at"]

    def get_permissions(self):
        """
        - Eliminar y reasignar: solo managers
        - Todo lo demás: agentes y managers (con restricción por objeto)
        """
        if self.action in ["destroy", "change_assigned"]:
            return [IsManager()]
        return [IsAgentOrManager()]

    def get_queryset(self):
        user = self.request.user
        base_qs = (
            Contact.objects.select_related("assigned_to")
            .annotate(interaction_count=Count("interactions"))
        )
        # Managers ven todos los contactos
        if user.is_superuser or user.groups.filter(name="managers").exists():
            return base_qs.all()
        # Agentes solo ven los suyos
        return base_qs.filter(assigned_to=user)

    def get_serializer_class(self):
        if self.action == "list":
            return ContactListSerializer
        return ContactSerializer

    def perform_create(self, serializer):
        if not serializer.validated_data.get("assigned_to"):
            serializer.save(assigned_to=self.request.user)
        else:
            serializer.save()

    @extend_schema(
        summary="Change contact status",
        request={"application/json": {"type": "object", "properties": {"status": {"type": "string"}}}},
        responses={200: ContactSerializer},
        tags=["Contacts"],
    )
    @action(detail=True, methods=["patch"], url_path="status")
    def change_status(self, request, pk=None):
        contact = self.get_object()
        new_status = request.data.get("status")

        if new_status not in Contact.Status.values:
            return Response(
                {"error": {"code": "validation_error", "message": f"Estado inválido: '{new_status}'."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contact.status = new_status
        contact.save(update_fields=["status", "updated_at"])
        serializer = ContactSerializer(contact, context={"request": request})
        return Response(serializer.data)

    @extend_schema(
        summary="My contacts",
        responses={200: ContactListSerializer(many=True)},
        tags=["Contacts"],
    )
    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request):
        qs = self.get_queryset().filter(assigned_to=request.user).order_by("-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ContactListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ContactListSerializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Reasignar contacto (solo managers)",
        request={"application/json": {"type": "object", "properties": {"assigned_to_id": {"type": "integer"}}}},
        responses={200: ContactSerializer},
        tags=["Contacts"],
    )
    @action(detail=True, methods=["patch"], url_path="assign")
    def change_assigned(self, request, pk=None):
        contact = self.get_object()
        from django.contrib.auth.models import User

        user_id = request.data.get("assigned_to_id")
        try:
            agent = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": {"code": "not_found", "message": f"Usuario {user_id} no existe."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        contact.assigned_to = agent
        contact.save(update_fields=["assigned_to", "updated_at"])
        serializer = ContactSerializer(contact, context={"request": request})
        return Response(serializer.data)
