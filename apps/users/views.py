from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from django.utils import timezone

from .models import MotardProfile, OwnerProfile, SupportTicket, User
from .serializers import (
    MotardProfileSerializer,
    OwnerProfileSerializer,
    RegisterSerializer,
    SupportTicketSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

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
