from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.users.models import User
from service.service_rides.logic import RideDispatchService

from . import services
from .models import Ride, RideRating
from .serializers import RideRatingSerializer, RideSerializer


class RideViewSet(viewsets.ModelViewSet):
    serializer_class = RideSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status"]

    def get_queryset(self):
        user = self.request.user
        qs = Ride.objects.select_related("client", "motard")
        if user.role == User.Role.OPERATOR or user.is_staff:
            return qs
        if user.role == User.Role.MOTARD:
            # Check active subscription eligibility via standalone service
            if RideDispatchService.is_motard_eligible_for_requests(user):
                return qs.filter(Q(motard=user) | Q(status=Ride.Status.REQUESTED))
            return qs.filter(motard=user)
        if user.role == User.Role.FLEET_MANAGER:
            # Courses des motards de la flotte gérée par ce gérant.
            return qs.filter(motard__assigned_motorcycle__fleet_manager=user).distinct()
        return qs.filter(client=user)

    def perform_create(self, serializer):
        """Création d'une demande de course : la logique métier (rôle client,
        unicité de la course active, statut REQUESTED) vit dans le service."""
        try:
            ride = services.create_ride_request(self.request.user, **serializer.validated_data)
        except DjangoValidationError as exc:
            raise ValidationError(exc.messages)
        serializer.instance = ride

    def _apply(self, service_fn, **kwargs):
        ride = self.get_object()
        try:
            ride = service_fn(ride, **kwargs)
        except DjangoValidationError as exc:
            raise ValidationError(exc.message)
        return Response(RideSerializer(ride).data)

    @action(detail=False, methods=["get"])
    def current(self, request):
        """Course active du client connecté (REQUESTED/ACCEPTED/ONGOING) + position du motard."""
        ride = (
            Ride.objects.select_related("motard")
            .filter(client=request.user, status__in=services.ACTIVE_RIDE_STATUSES)
            .order_by("-requested_at")
            .first()
        )
        if ride is None:
            return Response({"ride": None})

        data = RideSerializer(ride).data
        # Dernière position connue du motard assigné (pour le suivi temps réel).
        if ride.motard_id:
            from apps.geoloc.services import latest_position
            ping = latest_position(ride.motard)
            data["motard_position"] = (
                {"latitude": float(ping.latitude), "longitude": float(ping.longitude)}
                if ping else None
            )
        return Response({"ride": data})

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        return self._apply(services.accept_ride, motard=request.user)

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        return self._apply(services.start_ride)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        return self._apply(services.complete_ride, agreed_price=request.data.get("agreed_price"))

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        return self._apply(services.cancel_ride)


class RideRatingViewSet(viewsets.ModelViewSet):
    serializer_class = RideRatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return RideRating.objects.select_related("ride", "rated_by").filter(
            Q(ride__client=user) | Q(ride__motard=user)
        )

    def perform_create(self, serializer):
        serializer.save(rated_by=self.request.user)
