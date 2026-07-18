from django.conf import settings
from django.db import models


class Motorcycle(models.Model):
    class OwnershipType(models.TextChoices):
        OWNER_FLEET = "owner_fleet", "Flotte d'un propriétaire (gérance)"
        PLATFORM_FLEET = "platform_fleet", "Flotte Go-Mboka (allocation)"
        SELF_OWNED = "self_owned", "Propriété du motard (abonnement)"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Disponible"
        ASSIGNED = "assigned", "Assignée"
        MAINTENANCE = "maintenance", "En maintenance"
        RETIRED = "retired", "Retirée"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="motorcycles", limit_choices_to={"role": "owner"},
    )
    fleet_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="managed_motorcycles", limit_choices_to={"role": "fleet_manager"},
        verbose_name="gérant de flotte",
        help_text="Gérant Go-Mboka en charge du suivi quotidien de cette moto (gérance et allocation).",
    )
    ownership_type = models.CharField(max_length=20, choices=OwnershipType.choices)
    plate_number = models.CharField("plaque d'immatriculation", max_length=20, unique=True)
    device_id = models.CharField("ID du tracker (IMEI)", max_length=50, unique=True, blank=True, null=True)

    # Object Attributes
    brand = models.CharField("marque", max_length=50, blank=True)
    model_style = models.CharField("style/modèle", max_length=100, blank=True)
    acquisition_date = models.DateField("date d'acquisition", null=True, blank=True)
    chassis_number = models.CharField("numéro de châssis/VIN", max_length=100, unique=True, blank=True, null=True)
    color = models.CharField("couleur", max_length=50, blank=True)
    general_condition = models.IntegerField("état général (/10)", default=10)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    assigned_motard = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="assigned_motorcycle", limit_choices_to={"role": "motard"},
    )
    commission_rate = models.DecimalField(
        "taux de commission (%)", max_digits=5, decimal_places=2, default=0,
        help_text="Commission Go-Mboka prélevée sur les revenus générés par cette moto.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["plate_number"]

    def __str__(self):
        return f"{self.plate_number} - {self.brand} {self.model_style}"


class MotardTrial(models.Model):
    class TrialResult(models.TextChoices):
        PENDING = "pending", "En cours"
        VALIDATED = "validated", "Validé"
        REJECTED = "rejected", "Refusé"
        EXTENDED = "extended", "Prolongé"

    motard = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trials"
    )
    motorcycle = models.ForeignKey(
        Motorcycle, on_delete=models.CASCADE, related_name="trial_periods"
    )
    start_date = models.DateField()
    end_date = models.DateField()

    # Performance Criteria
    min_rides_required = models.PositiveIntegerField("courses min. requises", default=0)
    min_rating_required = models.DecimalField("note min. requise", max_digits=3, decimal_places=2, default=0)

    result = models.CharField(
        max_length=20, choices=TrialResult.choices, default=TrialResult.PENDING
    )
    final_notes = models.TextField("observations finales", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Essai de {self.motard} sur {self.motorcycle}"


class TrialDailyLog(models.Model):
    trial = models.ForeignKey(
        MotardTrial, on_delete=models.CASCADE, related_name="daily_logs"
    )
    date = models.DateField()
    return_time = models.TimeField("heure de retour")
    amount_paid = models.DecimalField("somme versée", max_digits=10, decimal_places=2)
    is_payment_complete = models.BooleanField("versement complet", default=True)
    motard_explanation = models.TextField("explications / plaintes", blank=True)
    bike_condition_score = models.PositiveIntegerField(
        "état de la moto (/10)", default=10
    )
    manager_notes = models.TextField("notes du gérant", blank=True)

    class Meta:
        unique_together = ('trial', 'date')

    def __str__(self):
        return f"Log {self.date} pour {self.trial}"


class Agreement(models.Model):
    class AgreementType(models.TextChoices):
        RENTAL = "rental", "Location Simple (Rental)"
        HIRE_PURCHASE = "hire_purchase", "Location-Vente (Hire Purchase)"

    class PaymentFrequency(models.TextChoices):
        DAILY = "daily", "Journalier"
        WEEKLY = "weekly", "Hebdomadaire"

    motard = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agreements"
    )
    motorcycle = models.ForeignKey(
        Motorcycle, on_delete=models.CASCADE, related_name="agreements"
    )
    agreement_type = models.CharField(max_length=20, choices=AgreementType.choices)
    frequency = models.CharField(max_length=20, choices=PaymentFrequency.choices)
    periodic_amount = models.DecimalField("montant périodique", max_digits=10, decimal_places=2)

    # Hire Purchase specific
    target_total_amount = models.DecimalField(
        "somme totale pour propriété", max_digits=10, decimal_places=2, null=True, blank=True
    )
    amount_already_paid = models.DecimalField("montant déjà versé", max_digits=10, decimal_places=2, default=0)

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contrat {self.agreement_type} - {self.motard} ({self.motorcycle.plate_number})"

# Keep the following models as they were, just updating references if needed.
class FleetRemittance(models.Model):
    motorcycle = models.ForeignKey(Motorcycle, on_delete=models.CASCADE, related_name="remittances")
    period_start = models.DateField()
    period_end = models.DateField()
    gross_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reversement {self.motorcycle} ({self.period_start} → {self.period_end})"

