## crm_service\apps\contacts\serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Contact


class AssignedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]
        read_only_fields = fields


class ContactSerializer(serializers.ModelSerializer):
    assigned_to = AssignedUserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="assigned_to",
        write_only=True,
        required=False,
        allow_null=True,
    )
    full_name = serializers.CharField(read_only=True)
    interaction_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Contact
        fields = [
            "id",
            "first_name",
            "last_name",
            "full_name",
            "email",
            "phone",
            "company",
            "status",
            "source",
            "assigned_to",
            "assigned_to_id",
            "notes",
            "interaction_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "full_name", "interaction_count"]

    def validate_email(self, value):
        qs = Contact.objects.filter(email=value)
        instance = self.instance
        if instance:
            qs = qs.exclude(pk=instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A contact with this email already exists.")
        return value


class ContactListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Contact
        fields = ["id", "full_name", "email", "company", "status", "source", "created_at"]
