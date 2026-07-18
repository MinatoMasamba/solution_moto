from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.users.models import User

from . import services
from .models import Agreement, FleetRemittance, MotardTrial, Motorcycle, TrialDailyLog
from .serializers import (
    AgreementSerializer,
    FleetRemittanceSerializer,
    MotardTrialSerializer,
    MotorcycleSerializer,
    TrialDailyLogSerializer,
)


def motorcycles_visible_to(user):
    qs = Motorcycle.objects.all()
    if user.role == User.Role.OPERATOR or user.is_staff:
        return qs
    if user.role == User.Role.FLEET_MANAGER:
        return qs.filter(fleet_manager=user)
    if user.role == User.Role.OWNER:
        return qs.filter(owner=user)
    if user.role == User.Role.MOTARD:
        return qs.filter(assigned_motard=user)
    return qs.none()


class MotorcycleViewSet(viewsets.ModelViewSet):
    serializer_class = MotorcycleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "ownership_type"]

    def get_queryset(self):
        return motorcycles_visible_to(self.request.user).select_related(
            "owner", "fleet_manager", "assigned_motard"
        )

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        motorcycle = self.get_object()
        motard = User.objects.filter(pk=request.data.get("motard_id"), role=User.Role.MOTARD).first()
        if motard is None:
            raise ValidationError("Motard introuvable.")
        try:
            motorcycle = services.assign_motard(motorcycle, motard)
        except DjangoValidationError as exc:
            raise ValidationError(exc.message)
        return Response(MotorcycleSerializer(motorcycle).data)

    @action(detail=True, methods=["post"])
    def release(self, request, pk=None):
        motorcycle = services.release_motard(self.get_object())
        return Response(MotorcycleSerializer(motorcycle).data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def assign_manager(self, request, pk=None):
        motorcycle = self.get_object()
        manager = User.objects.filter(
            pk=request.data.get("fleet_manager_id"), role=User.Role.FLEET_MANAGER
        ).first()
        if manager is None:
            raise ValidationError("Gérant de flotte introuvable.")
        motorcycle = services.assign_manager(motorcycle, manager)
        return Response(MotorcycleSerializer(motorcycle).data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def release_manager(self, request, pk=None):
        motorcycle = services.release_manager(self.get_object())
        return Response(MotorcycleSerializer(motorcycle).data)


class FleetRemittanceViewSet(viewsets.ModelViewSet):
    serializer_class = FleetRemittanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = FleetRemittance.objects.select_related("motorcycle").order_by("-period_end", "id")
        if user.role == User.Role.OPERATOR or user.is_staff:
            return qs
        return qs.filter(motorcycle__in=motorcycles_visible_to(user))


class MotardTrialViewSet(viewsets.ModelViewSet):
    serializer_class = MotardTrialSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["result"]

    def get_queryset(self):
        user = self.request.user
        qs = MotardTrial.objects.select_related("motard", "motorcycle")
        if user.role == User.Role.OPERATOR or user.is_staff:
            return qs
        if user.role == User.Role.MOTARD:
            return qs.filter(motard=user)
        return qs.filter(motorcycle__in=motorcycles_visible_to(user))

    def perform_create(self, serializer):
        motorcycle = serializer.validated_data["motorcycle"]
        user = self.request.user
        if not (user.role == User.Role.OPERATOR or user.is_staff) and motorcycle not in motorcycles_visible_to(user):
            raise ValidationError("Vous ne gérez pas cette moto.")
        serializer.save()


class TrialDailyLogViewSet(viewsets.ModelViewSet):
    serializer_class = TrialDailyLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = TrialDailyLog.objects.select_related("trial", "trial__motorcycle", "trial__motard")
        if user.role == User.Role.OPERATOR or user.is_staff:
            return qs
        if user.role == User.Role.MOTARD:
            return qs.filter(trial__motard=user)
        return qs.filter(trial__motorcycle__in=motorcycles_visible_to(user))

    def perform_create(self, serializer):
        trial = serializer.validated_data["trial"]
        user = self.request.user
        if not (user.role == User.Role.OPERATOR or user.is_staff) and trial.motorcycle not in motorcycles_visible_to(user):
            raise ValidationError("Vous ne gérez pas la moto liée à cet essai.")
        serializer.save()


class AgreementViewSet(viewsets.ModelViewSet):
    serializer_class = AgreementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["agreement_type", "is_active"]

    def get_queryset(self):
        user = self.request.user
        qs = Agreement.objects.select_related("motard", "motorcycle")
        if user.role == User.Role.OPERATOR or user.is_staff:
            return qs
        if user.role == User.Role.MOTARD:
            return qs.filter(motard=user)
        return qs.filter(motorcycle__in=motorcycles_visible_to(user))

    def perform_create(self, serializer):
        motorcycle = serializer.validated_data["motorcycle"]
        user = self.request.user
        if not (user.role == User.Role.OPERATOR or user.is_staff) and motorcycle not in motorcycles_visible_to(user):
            raise ValidationError("Vous ne gérez pas cette moto.")
        serializer.save()
