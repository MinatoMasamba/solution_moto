from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.models import User

from . import services
from .models import LocationPing
from .serializers import LocationPingSerializer


class LocationPingViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = LocationPingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["user", "ride"]

    def get_queryset(self):
        user = self.request.user
        qs = LocationPing.objects.select_related("user", "ride")
        if user.role == User.Role.OPERATOR or user.is_staff:
            return qs
        return qs.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def latest(self, request):
        ping = services.latest_position(request.user)
        if ping is None:
            return Response(status=204)
        return Response(LocationPingSerializer(ping).data)

    @action(detail=False, methods=["get"])
    def fleet(self, request):
        """Dernière position de chaque motard visible (carte temps réel)."""
        positions = services.latest_positions_for(request.user)
        return Response({"count": len(positions), "positions": positions})
