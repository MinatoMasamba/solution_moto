from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone_number, password, **extra_fields):
        if not phone_number:
            raise ValueError("Le numéro de téléphone est obligatoire.")
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.OPERATOR)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superuser doit avoir is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superuser doit avoir is_superuser=True.")
        return self._create_user(phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        CLIENT = "client", "Client"
        MOTARD = "motard", "Motard"
        OWNER = "owner", "Propriétaire de motos"
        FLEET_MANAGER = "fleet_manager", "Gérant de flotte"
        OPERATOR = "operator", "Opérateur"

    phone_number = models.CharField("numéro de téléphone", max_length=20, unique=True)
    email = models.EmailField("email", blank=True)
    first_name = models.CharField("prénom", max_length=150, blank=True)
    last_name = models.CharField("nom", max_length=150, blank=True)
    post_nom = models.CharField("post-nom", max_length=150, blank=True)
    role = models.CharField("rôle", max_length=20, choices=Role.choices, default=Role.CLIENT)
    is_verified = models.BooleanField("vérifié", default=False)
    is_active = models.BooleanField("actif", default=True)
    is_staff = models.BooleanField("accès admin", default=False)
    date_joined = models.DateTimeField("date d'inscription", default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"

    def __str__(self):
        return f"{self.get_full_name() or self.phone_number} ({self.get_role_display()})"

    def get_full_name(self):
        return " ".join(part for part in [self.first_name, self.last_name, self.post_nom] if part).strip()

    def get_short_name(self):
        return self.first_name or self.phone_number


PROVINCE_CHOICES = [
    ("kinshasa", "Kinshasa"),
    ("kongo_central", "Kongo-Central"),
    ("kwango", "Kwango"),
    ("kwilu", "Kwilu"),
    ("mai_ndombe", "Mai-Ndombe"),
    ("kasai", "Kasaï"),
    ("kasai_central", "Kasaï-Central"),
    ("kasai_oriental", "Kasaï-Oriental"),
    ("lomami", "Lomami"),
    ("sankuru", "Sankuru"),
    ("maniema", "Maniema"),
    ("sud_kivu", "Sud-Kivu"),
    ("nord_kivu", "Nord-Kivu"),
    ("ituri", "Ituri"),
    ("haut_uele", "Haut-Uele"),
    ("bas_uele", "Bas-Uele"),
    ("tshopo", "Tshopo"),
    ("tshuapa", "Tshuapa"),
    ("equateur", "Équateur"),
    ("sud_ubangi", "Sud-Ubangi"),
    ("nord_ubangi", "Nord-Ubangi"),
    ("mongala", "Mongala"),
    ("tanganyika", "Tanganyika"),
    ("haut_lomami", "Haut-Lomami"),
    ("lualaba", "Lualaba"),
    ("haut_katanga", "Haut-Katanga"),
]


class MotardProfile(models.Model):
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = "active", "Actif"
        TRIAL = "trial", "En essai"
        EXPIRED = "expired", "Expiré"
        SUSPENDED = "suspended", "Suspendu"

    class ApplicationStatus(models.TextChoices):
        PENDING = "pending", "En attente"
        APPROVED = "approved", "Validé"
        REJECTED = "rejected", "Rejeté"

    class Sexe(models.TextChoices):
        M = "M", "Masculin"
        F = "F", "Féminin"

    class TypePieceIdentite(models.TextChoices):
        CARTE_ELECTEUR = "CARTE_ELECTEUR", "Carte d'électeur"
        CARTE_NATIONALE = "CARTE_NATIONALE", "Carte nationale d'identité"
        PASSEPORT = "PASSEPORT", "Passeport"
        PERMIS_CONDUIRE = "PERMIS_CONDUIRE", "Permis de conduire"
        LIVRET_TRAVAIL = "LIVRET_TRAVAIL", "Livret de travail"
        AUTRE = "AUTRE", "Autre document officiel"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="motard_profile")
    license_number = models.CharField("numéro de permis", max_length=50, blank=True)
    id_card_number = models.CharField("numéro pièce d'identité", max_length=50, blank=True)
    photo = models.ImageField("photo de profil", upload_to="motards/photos/", blank=True, null=True)
    subscription_status = models.CharField(
        max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.EXPIRED
    )
    subscription_expires_at = models.DateTimeField(null=True, blank=True)
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    is_available = models.BooleanField("disponible", default=False)

    application_status = models.CharField(
        "statut du dossier", max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.PENDING
    )

    # Adresse de résidence
    province = models.CharField("province", max_length=30, choices=PROVINCE_CHOICES, blank=True)
    ville = models.CharField("ville / territoire", max_length=100, blank=True)
    commune = models.CharField("commune / secteur", max_length=100, blank=True)
    quartier = models.CharField("quartier", max_length=100, blank=True)
    avenue = models.CharField("avenue / rue", max_length=150, blank=True)
    numero_maison = models.CharField("numéro de la maison", max_length=20, blank=True)
    reference_adresse = models.CharField("référence / point de repère", max_length=200, blank=True)

    # Identité civile
    date_naissance = models.DateField("date de naissance", null=True, blank=True)
    sexe = models.CharField("sexe", max_length=1, choices=Sexe.choices, blank=True)

    # Pièce d'identité
    type_piece_identite = models.CharField(
        "type de pièce d'identité", max_length=20, choices=TypePieceIdentite.choices, blank=True
    )
    date_expiration_piece = models.DateField("date d'expiration de la pièce", null=True, blank=True)
    photo_piece_identite = models.FileField(
        "photo/scan de la pièce d'identité", upload_to="motards/pieces_identite/", blank=True, null=True
    )
    permis_conduire_photo = models.FileField(
        "permis de conduire (recto-verso)", upload_to="motards/permis/", blank=True, null=True
    )

    class Meta:
        verbose_name = "profil motard"
        verbose_name_plural = "profils motards"

    def __str__(self):
        return f"Profil motard de {self.user}"


class OwnerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="owner_profile")
    company_name = models.CharField("nom de l'entreprise", max_length=150, blank=True)
    id_card_number = models.CharField("numéro pièce d'identité", max_length=50, blank=True)

    class Meta:
        verbose_name = "profil propriétaire"
        verbose_name_plural = "profils propriétaires"

    def __str__(self):
        return f"Profil propriétaire de {self.user}"


class SupportTicket(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Basse"
        MEDIUM = "medium", "Moyenne"
        HIGH = "high", "Haute"

    class Status(models.TextChoices):
        OPEN = "open", "Ouvert"
        IN_PROGRESS = "in_progress", "En cours"
        RESOLVED = "resolved", "Résolu"

    requester = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="support_tickets"
    )
    subject = models.CharField("sujet", max_length=200)
    message = models.TextField("message", blank=True)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "ticket support"
        verbose_name_plural = "tickets support"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_status_display()}] {self.subject} — {self.requester}"
