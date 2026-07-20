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


class PaymentMethod(models.Model):
    """Moyen de paiement lié au compte : Mobile Money ou compte bancaire.
    Sert à recevoir les reversements (propriétaire) ou les retraits (motard)."""

    class Kind(models.TextChoices):
        MOBILE_MONEY = "mobile_money", "Mobile Money"
        BANK = "bank", "Compte bancaire"

    class MobileProvider(models.TextChoices):
        AIRTEL_MONEY = "airtel_money", "Airtel Money"
        MPESA = "mpesa", "M-Pesa"
        ORANGE_MONEY = "orange_money", "Orange Money"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_methods"
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)

    # Mobile Money
    provider = models.CharField("opérateur", max_length=20, choices=MobileProvider.choices, blank=True)
    phone_number = models.CharField("numéro mobile money", max_length=20, blank=True)

    # Compte bancaire
    bank_name = models.CharField("banque", max_length=100, blank=True)
    account_number = models.CharField("numéro de compte", max_length=50, blank=True)
    account_holder = models.CharField("titulaire du compte", max_length=150, blank=True)

    is_default = models.BooleanField("par défaut", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "moyen de paiement"
        verbose_name_plural = "moyens de paiement"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        if self.kind == self.Kind.MOBILE_MONEY:
            return f"{self.get_provider_display()} · {self.phone_number}"
        return f"{self.bank_name} · {self.account_number}"
