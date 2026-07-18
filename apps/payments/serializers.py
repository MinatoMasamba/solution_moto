from rest_framework import serializers

from .models import Payment, Subscription


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
