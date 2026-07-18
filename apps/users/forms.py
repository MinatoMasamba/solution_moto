from django import forms

from .models import MotardProfile, PROVINCE_CHOICES, User

MAX_DOCUMENT_SIZE = 5 * 1024 * 1024
MAX_PHOTO_SIZE = 2 * 1024 * 1024


class ChauffeurLoginForm(forms.Form):
    phone_number = forms.CharField(label="Numéro de téléphone", max_length=20)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)


class ChauffeurQuickRegistrationForm(forms.Form):
    """Inscription motard simplifiée (design « Auth Motard »).

    Les documents (permis, pièce d'identité) sont téléversés plus tard, lors de
    la vérification par un gérant — d'où un dossier créé en statut PENDING.
    """

    prenom = forms.CharField(label="Prénom", max_length=150)
    nom = forms.CharField(label="Nom", max_length=150)
    phone_number = forms.CharField(label="Téléphone", max_length=20)
    commune = forms.CharField(label="Commune", max_length=100, required=False)
    moto_type = forms.CharField(label="Type de moto", max_length=120, required=False)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput, min_length=8)

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"].strip()
        if User.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return phone_number

    def save(self):
        data = self.cleaned_data
        user = User(
            phone_number=data["phone_number"],
            first_name=data["prenom"],
            last_name=data["nom"],
            role=User.Role.MOTARD,
        )
        user.set_password(data["password"])
        user.save()
        MotardProfile.objects.create(
            user=user,
            commune=data.get("commune", ""),
            application_status=MotardProfile.ApplicationStatus.PENDING,
        )
        return user


class ChauffeurRegistrationForm(forms.Form):
    # Étape 1 — Identité & sécurité
    prenom = forms.CharField(label="Prénom", max_length=150)
    nom = forms.CharField(label="Nom", max_length=150)
    post_nom = forms.CharField(label="Post-nom", max_length=150)
    email = forms.EmailField(label="Email")
    phone_number = forms.CharField(label="Numéro de téléphone (WhatsApp)", max_length=20)
    password = forms.CharField(label="Mot de passe", widget=forms.PasswordInput, min_length=8)
    password_confirm = forms.CharField(label="Confirmer le mot de passe", widget=forms.PasswordInput, min_length=8)

    # Étape 2 — Adresse & identité civile
    province = forms.ChoiceField(label="Province", choices=PROVINCE_CHOICES)
    ville = forms.CharField(label="Ville / Territoire", max_length=100)
    commune = forms.CharField(label="Commune / Secteur", max_length=100, required=False)
    quartier = forms.CharField(label="Quartier", max_length=100)
    avenue = forms.CharField(label="Avenue / Rue", max_length=150)
    numero_maison = forms.CharField(label="Numéro de la maison", max_length=20)
    reference_adresse = forms.CharField(label="Référence / point de repère", max_length=200, required=False)
    date_naissance = forms.DateField(label="Date de naissance")
    sexe = forms.ChoiceField(label="Sexe", choices=MotardProfile.Sexe.choices)

    # Étape 3 — Documents
    type_piece_identite = forms.ChoiceField(
        label="Type de pièce d'identité", choices=MotardProfile.TypePieceIdentite.choices
    )
    numero_piece_identite = forms.CharField(label="Numéro de la pièce", max_length=50)
    date_expiration_piece = forms.DateField(label="Date d'expiration de la pièce", required=False)
    photo_piece_identite = forms.FileField(label="Photo / scan de la pièce d'identité")
    permis_conduire = forms.FileField(label="Permis de conduire (recto-verso)")
    photo_chauffeur = forms.ImageField(label="Photo d'identité (portrait)")

    def clean_phone_number(self):
        phone_number = self.cleaned_data["phone_number"].strip()
        if User.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("Ce numéro de téléphone est déjà utilisé.")
        return phone_number

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Les mots de passe ne correspondent pas.")
        return cleaned_data

    def clean_photo_piece_identite(self):
        return self._check_size(self.cleaned_data["photo_piece_identite"], MAX_DOCUMENT_SIZE, "5 MB")

    def clean_permis_conduire(self):
        return self._check_size(self.cleaned_data["permis_conduire"], MAX_DOCUMENT_SIZE, "5 MB")

    def clean_photo_chauffeur(self):
        return self._check_size(self.cleaned_data["photo_chauffeur"], MAX_PHOTO_SIZE, "2 MB")

    @staticmethod
    def _check_size(file_obj, max_size, label):
        if file_obj.size > max_size:
            raise forms.ValidationError(f"Le fichier ne doit pas dépasser {label}.")
        return file_obj

    def save(self):
        data = self.cleaned_data
        user = User(
            phone_number=data["phone_number"],
            email=data["email"],
            first_name=data["prenom"],
            last_name=data["nom"],
            post_nom=data["post_nom"],
            role=User.Role.MOTARD,
        )
        user.set_password(data["password"])
        user.save()

        MotardProfile.objects.create(
            user=user,
            id_card_number=data["numero_piece_identite"],
            photo=data["photo_chauffeur"],
            application_status=MotardProfile.ApplicationStatus.PENDING,
            province=data["province"],
            ville=data["ville"],
            commune=data["commune"],
            quartier=data["quartier"],
            avenue=data["avenue"],
            numero_maison=data["numero_maison"],
            reference_adresse=data["reference_adresse"],
            date_naissance=data["date_naissance"],
            sexe=data["sexe"],
            type_piece_identite=data["type_piece_identite"],
            date_expiration_piece=data.get("date_expiration_piece"),
            photo_piece_identite=data["photo_piece_identite"],
            permis_conduire_photo=data["permis_conduire"],
        )
        return user
