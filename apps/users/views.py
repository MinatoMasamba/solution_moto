from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView


class RegisterThrottle(AnonRateThrottle):
    scope = "auth_register"


class LoginThrottle(AnonRateThrottle):
    scope = "auth_login"

from django.utils import timezone

from django.db.models import Avg, Sum

from .models import MotardProfile, Notification, OwnerProfile, SavedPlace, SupportTicket, User
from .serializers import (
    MotardProfileSerializer,
    NotificationSerializer,
    OwnerProfileSerializer,
    RegisterSerializer,
    SavedPlaceSerializer,
    SupportTicketSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    throttle_classes = [RegisterThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=201,
        )


class ThrottledTokenObtainPairView(TokenObtainPairView):
    """Login JWT limité par IP (anti brute-force)."""

    throttle_classes = [LoginThrottle]


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        user = request.user
        for field in ("first_name", "last_name", "email"):
            if field in request.data:
                setattr(user, field, (request.data.get(field) or "").strip())
        user.save(update_fields=["first_name", "last_name", "email"])
        return Response(UserSerializer(user).data)


class MotardProfileViewSet(viewsets.ModelViewSet):
    serializer_class = MotardProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = MotardProfile.objects.select_related("user").order_by("id")
        if user.role == User.Role.OPERATOR or user.is_staff:
            return qs
        if user.role == User.Role.FLEET_MANAGER:
            # Motards assignés aux motos de la flotte gérée par ce gérant.
            return qs.filter(user__assigned_motorcycle__fleet_manager=user).distinct()
        return qs.filter(user=user)

    def _set_application_status(self, request, status_value):
        actor = request.user
        if not (actor.role == User.Role.OPERATOR or actor.is_staff):
            return Response({"detail": "Réservé à la Direction Générale."}, status=403)
        profile = self.get_object()
        profile.application_status = status_value
        profile.save(update_fields=["application_status"])
        return Response(MotardProfileSerializer(profile).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._set_application_status(request, MotardProfile.ApplicationStatus.APPROVED)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._set_application_status(request, MotardProfile.ApplicationStatus.REJECTED)


class OwnerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = OwnerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = OwnerProfile.objects.select_related("user")
        if user.role == User.Role.OPERATOR or user.is_staff:
            return qs
        return qs.filter(user=user)


class SupportTicketViewSet(viewsets.ModelViewSet):
    """Tickets support. Chaque utilisateur crée/voit les siens ; l'opérateur voit tout."""

    serializer_class = SupportTicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = SupportTicket.objects.select_related("requester")
        if user.role == User.Role.OPERATOR or user.is_staff:
            return qs
        return qs.filter(requester=user)

    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        actor = request.user
        if not (actor.role == User.Role.OPERATOR or actor.is_staff):
            return Response({"detail": "Réservé à la Direction Générale."}, status=403)
        ticket = self.get_object()
        ticket.status = SupportTicket.Status.RESOLVED
        ticket.resolved_at = timezone.now()
        ticket.save(update_fields=["status", "resolved_at"])
        return Response(SupportTicketSerializer(ticket).data)


class SavedPlaceViewSet(viewsets.ModelViewSet):
    """Lieux enregistrés du client connecté (CRUD, strictement scopé à l'utilisateur)."""

    serializer_class = SavedPlaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavedPlace.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationsView(APIView):
    """Boîte de notifications in-app de l'utilisateur connecté.
    GET  -> {"unread": n, "items": [30 dernières]}
    POST -> marque comme lues ({'ids': [...]} ou rien pour tout marquer)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        items = Notification.objects.filter(user=request.user)[:30]
        unread = Notification.objects.filter(user=request.user, read_at__isnull=True).count()
        return Response({
            "unread": unread,
            "items": NotificationSerializer(items, many=True).data,
        })

    def post(self, request):
        ids = request.data.get("ids")
        from .services import mark_notifications_read
        updated = mark_notifications_read(request.user, ids if isinstance(ids, list) else None)
        unread = Notification.objects.filter(user=request.user, read_at__isnull=True).count()
        return Response({"marked": updated, "unread": unread})


class ClientSummaryView(APIView):
    """Synthèse pour l'en-tête / accueil de l'app client : identité, note,
    nombre de courses, code de parrainage, filleuls, solde et courses offertes."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.rides.models import Ride, RideRating
        from apps.payments.models import WalletTransaction

        user = request.user
        rides_count = Ride.objects.filter(client=user, status=Ride.Status.COMPLETED).count()
        rating = RideRating.objects.filter(ride__client=user).aggregate(avg=Avg("score"))["avg"]
        balance = WalletTransaction.objects.filter(
            user=user, status=WalletTransaction.Status.SUCCESS
        ).aggregate(total=Sum("amount"))["total"] or 0
        referred = User.objects.filter(referred_by_code=user.referral_code).count() \
            if hasattr(User, "referred_by_code") else 0

        methods_count = user.payment_methods.count() if hasattr(user, "payment_methods") else 0
        MONTHS = ["", "janvier", "février", "mars", "avril", "mai", "juin",
                  "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        dj = user.date_joined
        member_since = f"{MONTHS[dj.month]} {dj.year}" if dj else None

        return Response({
            "name": user.get_full_name() or user.phone_number,
            "phone_number": user.phone_number,
            "rating": round(float(rating), 1) if rating else None,
            "rides_count": rides_count,
            "referral_code": user.referral_code,
            "referred_count": referred,
            "free_rides": 0,
            "wallet_balance": balance,
            "member_since": member_since,
            "payment_methods_count": methods_count,
        })
