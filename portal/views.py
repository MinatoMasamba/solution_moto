import re

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import OwnerProfile, User

from .services import DashboardService


# ══════════════════════════════════════════════════════════════════════════
# Helpers d'authentification web (session)
# ══════════════════════════════════════════════════════════════════════════

def _is_operator(user):
    return bool(user and user.is_authenticated and (user.role == User.Role.OPERATOR or user.is_staff))


def _is_manager(user):
    return bool(
        user and user.is_authenticated
        and (user.role == User.Role.FLEET_MANAGER or user.is_staff)
    )


def _is_owner(user):
    return bool(
        user and user.is_authenticated
        and (user.role == User.Role.OWNER or user.is_staff)
    )


# Mots-clés typiques des User-Agent de téléphones/tablettes.
_MOBILE_UA = re.compile(
    r"Mobi|Android|iPhone|iPad|iPod|Windows Phone|BlackBerry|Opera Mini|IEMobile|webOS",
    re.IGNORECASE,
)


def _is_mobile_request(request):
    """Décide si on sert la version mobile.

    Priorité au paramètre explicite ``?view=mobile|web`` (utile pour tester et
    partager un lien), sinon détection automatique via le User-Agent.
    """
    forced = (request.GET.get("view") or "").strip().lower()
    if forced in ("mobile", "phone"):
        return True
    if forced in ("web", "pc", "desktop"):
        return False
    ua = request.META.get("HTTP_USER_AGENT", "")
    return bool(_MOBILE_UA.search(ua))


def _authenticate_identifier(request, identifier, password):
    """Authentifie par numéro de téléphone (USERNAME_FIELD) ou, à défaut, par e-mail."""
    identifier = (identifier or "").strip()
    user = authenticate(request, username=identifier, password=password)
    if user is None and "@" in identifier:
        match = User.objects.filter(email__iexact=identifier).first()
        if match is not None:
            user = authenticate(request, username=match.phone_number, password=password)
    return user


class RoleRequiredMixin:
    """Réserve une page à des rôles donnés (les opérateurs/staff passent toujours)."""

    required_roles = ()
    login_url = "portal:login"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect(self.login_url)
        if not (user.is_staff or user.role in self.required_roles):
            messages.error(request, "Accès non autorisé pour votre profil.")
            return redirect(self.login_url)
        return super().dispatch(request, *args, **kwargs)


# ══════════════════════════════════════════════════════════════════════════
# Portail public (existant)
# ══════════════════════════════════════════════════════════════════════════

class HomeView(TemplateView):
    template_name = "portal/home.html"


class RegisterPageView(TemplateView):
    template_name = "portal/register.html"


class LoginPageView(TemplateView):
    template_name = "portal/login.html"


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("portal:home")

    def get(self, request):
        logout(request)
        return redirect("portal:home")


class AppRedirectView(View):
    """« Passer à l'app » : route l'utilisateur connecté vers sa console selon son rôle."""

    def get(self, request):
        user = request.user
        if not user.is_authenticated:
            return redirect("chauffeur:chauffeur_login")
        if _is_operator(user):
            return redirect("portal:direction_dashboard")
        if user.role == User.Role.FLEET_MANAGER:
            return redirect("portal:gerance_dashboard")
        if user.role == User.Role.OWNER:
            return redirect("portal:proprietaire_dashboard")
        if user.role == User.Role.CLIENT:
            return redirect("portal:client_app")
        return redirect("portal:home")


# ══════════════════════════════════════════════════════════════════════════
# Direction Générale (opérateur) — pages
# ══════════════════════════════════════════════════════════════════════════

class DirectionLoginView(View):
    template_name = "direction/login.html"

    def get(self, request):
        if _is_operator(request.user):
            return redirect("portal:direction_dashboard")
        return render(request, self.template_name)

    def post(self, request):
        user = _authenticate_identifier(
            request, request.POST.get("identifier"), request.POST.get("password")
        )
        if user is not None and _is_operator(user):
            login(request, user)
            return redirect("portal:direction_dashboard")
        messages.error(request, "Identifiants invalides ou accès réservé à la Direction Générale.")
        return render(request, self.template_name, status=401)


class DirectionDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "direction/dashboard.html"
    required_roles = (User.Role.OPERATOR,)
    login_url = "portal:direction_login"


class DirectionConsoleView(RoleRequiredMixin, TemplateView):
    template_name = "direction/console.html"
    required_roles = (User.Role.OPERATOR,)
    login_url = "portal:direction_login"


# ══════════════════════════════════════════════════════════════════════════
# Gérance (gérant de flotte) — pages
# ══════════════════════════════════════════════════════════════════════════

class GeranceAuthView(View):
    template_name = "gerance/auth.html"

    def get(self, request):
        if _is_manager(request.user):
            return redirect("portal:gerance_dashboard")
        return render(request, self.template_name, {"active_tab": "login"})

    def post(self, request):
        if request.POST.get("action") == "register":
            return self._register(request)
        return self._login(request)

    def _login(self, request):
        user = _authenticate_identifier(
            request, request.POST.get("identifier"), request.POST.get("password")
        )
        if user is not None and _is_manager(user):
            login(request, user)
            return redirect("portal:gerance_dashboard")
        messages.error(request, "Identifiants invalides ou accès réservé aux gérants.")
        return render(request, self.template_name, {"active_tab": "login"}, status=401)

    def _register(self, request):
        data = request.POST
        ctx = {"active_tab": "create", "form_data": data}

        prenom = (data.get("prenom") or "").strip()
        nom = (data.get("nom") or "").strip()
        phone = (data.get("phone_number") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        if not all([prenom, nom, phone, password]):
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return render(request, self.template_name, ctx, status=400)
        if len(password) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
            return render(request, self.template_name, ctx, status=400)
        if User.objects.filter(phone_number=phone).exists():
            messages.error(request, "Ce numéro de téléphone est déjà utilisé.")
            return render(request, self.template_name, ctx, status=400)
        if email and User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Cette adresse e-mail est déjà utilisée.")
            return render(request, self.template_name, ctx, status=400)

        try:
            user = User(
                phone_number=phone, email=email, first_name=prenom, last_name=nom,
                role=User.Role.FLEET_MANAGER, is_verified=False,
            )
            user.set_password(password)
            user.save()
        except IntegrityError:
            messages.error(request, "Un compte existe déjà avec ces informations.")
            return render(request, self.template_name, ctx, status=400)

        messages.success(
            request,
            "Compte gérant créé. Il sera activé après validation par la Direction Générale.",
        )
        return redirect("portal:gerance_auth")


class GeranceDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "gerance/dashboard.html"
    required_roles = (User.Role.FLEET_MANAGER,)
    login_url = "portal:gerance_auth"


# ══════════════════════════════════════════════════════════════════════════
# Propriétaire (owner de flotte) — pages
# ══════════════════════════════════════════════════════════════════════════

class ProprietaireAuthView(View):
    template_name = "proprietaire/auth.html"

    def get(self, request):
        if _is_owner(request.user):
            return redirect("portal:proprietaire_dashboard")
        return render(request, self.template_name, {"active_tab": "login"})

    def post(self, request):
        if request.POST.get("action") == "register":
            return self._register(request)
        return self._login(request)

    def _login(self, request):
        user = _authenticate_identifier(
            request, request.POST.get("identifier"), request.POST.get("password")
        )
        if user is not None and _is_owner(user):
            login(request, user)
            return redirect("portal:proprietaire_dashboard")
        messages.error(request, "Identifiants invalides ou accès réservé aux propriétaires.")
        return render(request, self.template_name, {"active_tab": "login"}, status=401)

    def _register(self, request):
        data = request.POST
        ctx = {"active_tab": "create", "form_data": data}

        prenom = (data.get("prenom") or "").strip()
        nom = (data.get("nom") or "").strip()
        phone = (data.get("phone_number") or "").strip()
        email = (data.get("email") or "").strip().lower()
        company = (data.get("company_name") or "").strip()
        password = data.get("password") or ""

        if not all([prenom, nom, phone, password]):
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return render(request, self.template_name, ctx, status=400)
        if len(password) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
            return render(request, self.template_name, ctx, status=400)
        if User.objects.filter(phone_number=phone).exists():
            messages.error(request, "Ce numéro de téléphone est déjà utilisé.")
            return render(request, self.template_name, ctx, status=400)
        if email and User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Cette adresse e-mail est déjà utilisée.")
            return render(request, self.template_name, ctx, status=400)

        try:
            user = User(
                phone_number=phone, email=email, first_name=prenom, last_name=nom,
                role=User.Role.OWNER, is_verified=False,
            )
            user.set_password(password)
            user.save()
            OwnerProfile.objects.get_or_create(
                user=user, defaults={"company_name": company}
            )
        except IntegrityError:
            messages.error(request, "Un compte existe déjà avec ces informations.")
            return render(request, self.template_name, ctx, status=400)

        messages.success(
            request,
            "Compte propriétaire créé. Il sera activé après validation par la Direction Générale.",
        )
        return render(request, self.template_name, {"active_tab": "login"})


class OwnerDashboardPageView(RoleRequiredMixin, TemplateView):
    """Espace propriétaire. Sert automatiquement la version mobile ou PC
    selon l'appareil (User-Agent), avec override ``?view=mobile|web``."""

    required_roles = (User.Role.OWNER,)
    login_url = "portal:proprietaire_auth"

    def get_template_names(self):
        if _is_mobile_request(self.request):
            return ["proprietaire/mobile.html"]
        return ["proprietaire/dashboard.html"]


class OwnerMobilePageView(RoleRequiredMixin, TemplateView):
    """Force la version mobile (lien direct /proprietaire/mobile/)."""

    template_name = "proprietaire/mobile.html"
    required_roles = (User.Role.OWNER,)
    login_url = "portal:proprietaire_auth"


# ══════════════════════════════════════════════════════════════════════════
# Client — app de commande de courses (mobile)
# ══════════════════════════════════════════════════════════════════════════

class ClientAppView(RoleRequiredMixin, TemplateView):
    """App client : commander une course, portefeuille, lieux, profil."""

    template_name = "client/app.html"
    required_roles = (User.Role.CLIENT,)
    login_url = "portal:login"


# ══════════════════════════════════════════════════════════════════════════
# API — permissions
# ══════════════════════════════════════════════════════════════════════════

class IsOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        return _is_operator(request.user)


class IsOwnerOrOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated
            and (user.role in (User.Role.OWNER, User.Role.OPERATOR) or user.is_staff)
        )


class IsFleetManagerOrOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        return _is_manager(request.user)


# ══════════════════════════════════════════════════════════════════════════
# API — tableaux de bord
# ══════════════════════════════════════════════════════════════════════════

class OperatorDashboardView(APIView):
    """Tableau de bord 1a — Directeur Général : vue globale de la plateforme."""

    permission_classes = [IsOperator]

    def get(self, request):
        return Response({
            "kpis": DashboardService.get_operator_kpis(),
            "activity": DashboardService.get_hourly_activity(),
            "top_motards": DashboardService.get_top_motards(),
        })


class OwnerDashboardView(APIView):
    permission_classes = [IsOwnerOrOperator]

    def get(self, request):
        user = request.user
        owner = user if user.role == User.Role.OWNER else None
        return Response({
            "kpis": DashboardService.get_owner_kpis(owner=owner),
            "commissions": DashboardService.get_fleet_commissions(owner=owner),
        })


class IsMotard(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.role == User.Role.MOTARD or user.is_staff))


class MotardDashboardView(APIView):
    """Tableau de bord de l'app Chauffeur (motard) — gains, courses, abonnement."""

    permission_classes = [IsMotard]

    def get(self, request):
        return Response({"kpis": DashboardService.get_motard_kpis(request.user)})


class FleetManagerDashboardView(APIView):
    """Tableau de bord 1b — Gérant : portefeuille de motos/motards suivi au quotidien."""

    permission_classes = [IsFleetManagerOrOperator]

    def get(self, request):
        user = request.user
        manager = user if user.role == User.Role.FLEET_MANAGER else None
        return Response({
            "kpis": DashboardService.get_manager_kpis(fleet_manager=manager),
            "fleet": DashboardService.get_manager_fleet_detail(fleet_manager=manager),
            "watch": DashboardService.get_manager_watchlist(fleet_manager=manager),
            "remittances": DashboardService.get_manager_remittances(fleet_manager=manager),
        })


class OperatorClientsView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        return Response(DashboardService.get_operator_clients())


class SupportRequestsView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        return Response(DashboardService.get_support_requests())


class OperatorGerantsView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        return Response(DashboardService.get_operator_gerants())


class OperatorCommissionsView(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        return Response({"commissions": DashboardService.get_fleet_commissions(owner=None)})


class NotificationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(DashboardService.get_notifications())


class ManagerPerformanceView(APIView):
    permission_classes = [IsFleetManagerOrOperator]

    def get(self, request):
        user = request.user
        manager = user if user.role == User.Role.FLEET_MANAGER else None
        return Response(DashboardService.get_manager_performance(fleet_manager=manager))


class PasswordChangeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old = request.data.get("old_password") or ""
        new = request.data.get("new_password") or ""
        new2 = request.data.get("new_password2") or ""
        if not request.user.check_password(old):
            return Response({"detail": "Mot de passe actuel incorrect."}, status=400)
        if new != new2:
            return Response({"detail": "Les mots de passe ne correspondent pas."}, status=400)
        if len(new) < 8:
            return Response({"detail": "Mot de passe trop court (min. 8 caractères)."}, status=400)
        request.user.set_password(new)
        request.user.save(update_fields=["password"])
        update_session_auth_hash(request, request.user)
        return Response({"ok": True})


def health_check(request):
    return JsonResponse({"status": "ok"})
