import json
import secrets

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View

# Importations ajoutées pour le dashboard client
from django.contrib.auth.decorators import login_required
from django.test import RequestFactory
from .views import ClientSummaryView
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from .forms import ChauffeurLoginForm, ChauffeurQuickRegistrationForm
from .models import User

RESET_CODE_TTL_SECONDS = 60 * 10

# Les deux vues rendent la même page (design « Auth Motard », onglets connexion / création).
CHAUFFEUR_AUTH_TEMPLATE = "chauffeur/chauffeur_auth/chauffeur_login.html"


class ChauffeurLoginView(View):
    template_name = CHAUFFEUR_AUTH_TEMPLATE

    def get(self, request):
        return render(request, self.template_name, {"active_tab": "login"})

    def post(self, request):
        form = ChauffeurLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["phone_number"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                login(request, user)
                if user.role == User.Role.MOTARD or user.is_staff:
                    return redirect("chauffeur:chauffeur_app")
                return redirect("portal:home")
            messages.error(request, "Numéro de téléphone ou mot de passe incorrect.")
        else:
            messages.error(request, "Veuillez renseigner votre numéro et votre mot de passe.")
        return render(request, self.template_name, {"active_tab": "login"}, status=401)


class ChauffeurAppView(View):
    """App du motard (session). Réservée au rôle MOTARD."""

    template_name = "chauffeur/chauffeur_web_mobile/app.html"

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect("chauffeur:chauffeur_login")
        if not (user.role == User.Role.MOTARD or user.is_staff):
            messages.error(request, "Accès réservé aux motards.")
            return redirect("chauffeur:chauffeur_login")
        return render(request, self.template_name)


class ChauffeurRegistrationView(View):
    template_name = CHAUFFEUR_AUTH_TEMPLATE

    def get(self, request):
        return render(request, self.template_name, {"active_tab": "create"})

    def post(self, request):
        form = ChauffeurQuickRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Inscription reçue. Votre dossier est en attente de validation par un gérant.",
            )
            return redirect("chauffeur:chauffeur_login")
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
        return render(
            request,
            self.template_name,
            {"active_tab": "create", "form_data": request.POST},
            status=400,
        )


def _reset_cache_key(email):
    return f"chauffeur-password-reset:{email}"


def chauffeur_password_reset_request(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Méthode non autorisée."}, status=405)
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Requête invalide."}, status=400)

    email = (data.get("email") or "").strip().lower()
    if not email:
        return JsonResponse({"ok": False, "error": "Adresse email requise."}, status=400)

    user = User.objects.filter(email__iexact=email).first()
    if user is not None:
        code = f"{secrets.randbelow(1_000_000):06d}"
        cache.set(_reset_cache_key(email), code, RESET_CODE_TTL_SECONDS)
        send_mail(
            "Go-Mboka — Code de réinitialisation",
            f"Votre code de réinitialisation est {code}. Il expire dans 10 minutes.",
            None,
            [email],
            fail_silently=True,
        )
    # Réponse identique que le compte existe ou non, pour ne pas révéler son existence.
    return JsonResponse({"ok": True})


def chauffeur_password_reset_confirm(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Méthode non autorisée."}, status=405)
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Requête invalide."}, status=400)

    email = (data.get("email") or "").strip().lower()
    code = (data.get("code") or "").strip()
    password = data.get("password") or ""
    password2 = data.get("password2") or ""

    if not all([email, code, password, password2]):
        return JsonResponse({"ok": False, "error": "Tous les champs sont requis."}, status=400)
    if password != password2:
        return JsonResponse({"ok": False, "error": "Les mots de passe ne correspondent pas."}, status=400)
    if len(password) < 8:
        return JsonResponse({"ok": False, "error": "Mot de passe trop court (min. 8 caractères)."}, status=400)

    cache_key = _reset_cache_key(email)
    if cache.get(cache_key) != code:
        return JsonResponse({"ok": False, "error": "Code invalide ou expiré."}, status=400)

    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        return JsonResponse({"ok": False, "error": "Code invalide ou expiré."}, status=400)

    user.set_password(password)
    user.save(update_fields=["password"])
    cache.delete(cache_key)
    return JsonResponse({"ok": True})

# Client-specific views
# L'app client fonctionnelle est servie par portal.views.ClientAppView
# (templates/client/app.html + gm-client.js). Cette ancienne route redirige
# vers elle pour éviter le doublon avec la maquette statique client_dashboard.html.
@login_required
def client_dashboard_view(request):
    from django.shortcuts import redirect
    return redirect('portal:client_app')

class ClientLoginView(LoginView):
    template_name = 'portal/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('portal:client_app')
