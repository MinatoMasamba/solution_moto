from rest_framework import serializers

from .models import Payment, PaymentMethod, Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ["id", "motard", "amount", "status", "period_start", "period_end", "created_at"]
        read_only_fields = ["id", "motard", "status", "period_start", "period_end", "created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id", "user", "subscription", "ride", "purpose", "provider",
            "amount", "status", "provider_transaction_id", "created_at", "confirmed_at",
        ]
        read_only_fields = ["id", "user", "status", "provider_transaction_id", "created_at", "confirmed_at"]


class PaymentMethodSerializer(serializers.ModelSerializer):
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    provider_display = serializers.CharField(source="get_provider_display", read_only=True)
    label = serializers.SerializerMethodField()

    class Meta:
        model = PaymentMethod
        fields = [
            "id", "kind", "kind_display", "provider", "provider_display", "phone_number",
            "bank_name", "account_number", "account_holder", "is_default", "label", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_label(self, obj):
        return str(obj)

    def validate(self, attrs):
        kind = attrs.get("kind", getattr(self.instance, "kind", None))
        if kind == PaymentMethod.Kind.MOBILE_MONEY:
            provider = attrs.get("provider", getattr(self.instance, "provider", ""))
            phone = attrs.get("phone_number", getattr(self.instance, "phone_number", ""))
            if not provider:
                raise serializers.ValidationError({"provider": "Opérateur requis pour Mobile Money."})
            if not phone:
                raise serializers.ValidationError({"phone_number": "Numéro Mobile Money requis."})
        elif kind == PaymentMethod.Kind.BANK:
            if not attrs.get("bank_name", getattr(self.instance, "bank_name", "")):
                raise serializers.ValidationError({"bank_name": "Nom de la banque requis."})
            if not attrs.get("account_number", getattr(self.instance, "account_number", "")):
                raise serializers.ValidationError({"account_number": "Numéro de compte requis."})
        else:
            raise serializers.ValidationError({"kind": "Type de moyen de paiement invalide."})
        return attrs
