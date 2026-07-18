from django.conf import settings
from django.db import models


class Provider(models.TextChoices):
    AIRTEL_MONEY = "airtel_money", "Airtel Money"
    MPESA = "mpesa", "M-Pesa"
    ORANGE_MONEY = "orange_money", "Orange Money"
    CASH = "cash", "Espèces"


class Subscription(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expirée"

    motard = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Abonnement de {self.motard} ({self.get_status_display()})"


class Payment(models.Model):
    class Purpose(models.TextChoices):
        SUBSCRIPTION = "subscription", "Abonnement motard"
        RIDE = "ride", "Course"
        FLEET_REMITTANCE = "fleet_remittance", "Reversement flotte"

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        SUCCESS = "success", "Réussi"
        FAILED = "failed", "Échoué"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    subscription = models.ForeignKey(
        Subscription, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )
    ride = models.ForeignKey(
        "rides.Ride", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )
    purpose = models.CharField(max_length=20, choices=Purpose.choices)
    provider = models.CharField(max_length=20, choices=Provider.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    provider_transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Paiement {self.amount} ({self.get_status_display()})"
