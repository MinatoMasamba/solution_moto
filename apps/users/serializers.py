from rest_framework import serializers

from .models import MotardProfile, OwnerProfile, SavedPlace, SupportTicket, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone_number", "email", "first_name", "last_name", "role", "is_verified", "date_joined"]
        read_only_fields = ["id", "is_verified", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "phone_number", "email", "first_name", "last_name", "role", "password"]

    def validate_role(self, value):
        if value == User.Role.OPERATOR:
            raise serializers.ValidationError("Ce rôle ne peut pas être choisi à l'inscription.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        # Crée automatiquement le profil lié selon le rôle.
        # MotardProfile démarre avec subscription_status='expired' par défaut :
        # le motard ne peut donc PAS recevoir de courses tant qu'un abonnement actif
        # n'a pas été enregistré par un opérateur.
        if user.role == User.Role.MOTARD:
            MotardProfile.objects.get_or_create(user=user)
        elif user.role == User.Role.OWNER:
            OwnerProfile.objects.get_or_create(user=user)
        return user


class MotardProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    application_status_display = serializers.CharField(source="get_application_status_display", read_only=True)

    class Meta:
        model = MotardProfile
        fields = [
            "id", "user", "license_number", "id_card_number", "photo",
            "subscription_status", "subscription_expires_at", "rating_average", "is_available",
            "application_status", "application_status_display", "commune",
        ]
        read_only_fields = ["id", "subscription_status", "subscription_expires_at", "rating_average"]


class OwnerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OwnerProfile
        fields = ["id", "user", "company_name", "id_card_number"]
        read_only_fields = ["id"]


class SupportTicketSerializer(serializers.ModelSerializer):
    requester_name = serializers.SerializerMethodField()
    requester_role = serializers.CharField(source="requester.get_role_display", read_only=True)
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            "id", "requester", "requester_name", "requester_role",
            "subject", "message", "priority", "priority_display",
            "status", "status_display", "created_at", "resolved_at",
        ]
        read_only_fields = ["id", "requester", "status", "created_at", "resolved_at"]

    def get_requester_name(self, obj):
        return obj.requester.get_full_name() or obj.requester.phone_number


class SavedPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedPlace
        fields = ["id", "label", "address", "latitude", "longitude", "icon", "created_at"]
        read_only_fields = ["id", "created_at"]
