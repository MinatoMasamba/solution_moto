from rest_framework import serializers

from .models import MotardProfile, OwnerProfile, User


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

    class Meta:
        model = MotardProfile
        fields = [
            "id", "user", "license_number", "id_card_number", "photo",
            "subscription_status", "subscription_expires_at", "rating_average", "is_available",
        ]
        read_only_fields = ["id", "subscription_status", "subscription_expires_at", "rating_average"]


class OwnerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OwnerProfile
        fields = ["id", "user", "company_name", "id_card_number"]
        read_only_fields = ["id"]
