from rest_framework import serializers

from .models import LocationPing


class LocationPingSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationPing
        fields = ["id", "user", "ride", "latitude", "longitude", "recorded_at"]
        read_only_fields = ["id", "user", "recorded_at"]
