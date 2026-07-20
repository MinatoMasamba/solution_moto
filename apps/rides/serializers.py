from rest_framework import serializers

from .models import Ride, RideRating


class RideSerializer(serializers.ModelSerializer):
    client_name = serializers.SerializerMethodField()
    motard_name = serializers.SerializerMethodField()

    class Meta:
        model = Ride
        fields = [
            "id", "client", "client_name", "motard", "motard_name", "status",
            "pickup_address", "pickup_latitude", "pickup_longitude",
            "dropoff_address", "dropoff_latitude", "dropoff_longitude",
            "agreed_price", "requested_at", "accepted_at", "started_at",
            "completed_at", "cancelled_at",
        ]
        read_only_fields = [
            "id", "client", "motard", "status", "requested_at", "accepted_at",
            "started_at", "completed_at", "cancelled_at",
        ]
        extra_kwargs = {
            # Le client commande à l'adresse ; les coordonnées (GPS départ,
            # destination géocodée) sont optionnelles et valent 0 par défaut.
            "pickup_latitude": {"required": False, "default": 0},
            "pickup_longitude": {"required": False, "default": 0},
            "dropoff_latitude": {"required": False, "default": 0},
            "dropoff_longitude": {"required": False, "default": 0},
        }

    def get_client_name(self, obj):
        return obj.client.get_full_name() or obj.client.phone_number if obj.client_id else None

    def get_motard_name(self, obj):
        return (obj.motard.get_full_name() or obj.motard.phone_number) if obj.motard_id else None


class RideRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideRating
        fields = ["id", "ride", "rated_by", "score", "comment", "created_at"]
        read_only_fields = ["id", "rated_by", "created_at"]
