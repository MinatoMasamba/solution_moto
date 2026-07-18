import logging
import math
from django.utils import timezone
from apps.users.models import User
from apps.rides.models import Ride
from apps.geoloc.models import LocationPing
from service.service_rides.logic import RideDispatchService

logger = logging.getLogger(__name__)

class MobileClientService:
    """
    Logic dedicated to mobile client requests: searching motards, estimating fares,
    and creating rides.
    """

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance between two points 
        on the earth (specified in decimal degrees)
        """
        # convert decimal degrees to radians 
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a)) 
        r = 6371 # Radius of earth in kilometers
        return c * r

    @classmethod
    def get_nearby_motards(cls, latitude, longitude, radius_km=3.0):
        """
        Find nearby available motards with an ACTIVE subscription.
        First falls back to PostgreSQL LocationPing if Redis is not configured.
        """
        # Filter motards according to the rule of gold (Active subscription + Available)
        eligible_motards = User.objects.filter(
            role=User.Role.MOTARD,
            motard_profile__subscription_status="active",
            motard_profile__is_available=True
        )

        nearby = []
        for motard in eligible_motards:
            # Get their latest GPS ping
            latest_ping = LocationPing.objects.filter(user=motard).order_by("-created_at").first()
            if not latest_ping:
                continue

            distance = cls.haversine_distance(
                latitude, longitude, 
                float(latest_ping.latitude), float(latest_ping.longitude)
            )

            if distance <= radius_km:
                moto = getattr(motard, "assigned_motorcycle", None)
                nearby.append({
                    "motard_id": motard.id,
                    "name": motard.get_full_name(),
                    "latitude": float(latest_ping.latitude),
                    "longitude": float(latest_ping.longitude),
                    "distance_km": round(distance, 2),
                    "motorcycle": {
                        "brand": moto.brand if moto else "Inconnue",
                        "plate": moto.plate_number if moto else "Sans plaque",
                    } if moto else None
                })

        # Sort by closest first
        nearby.sort(key=lambda x: x["distance_km"])
        return nearby

    @staticmethod
    def estimate_fare(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
        """
        Simple price estimation logic based on distance (assuming 1500 FC per km + 2000 FC base fare)
        """
        # Calculate straight-line distance (rough estimate)
        lat1, lon1, lat2, lon2 = map(math.radians, [pickup_lat, pickup_lng, dropoff_lat, dropoff_lng])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance_km = c * 6371

        # Base fare 2000 FC + 1500 FC per KM
        estimated_price_fc = 2000 + (distance_km * 1500)
        # Round to nearest 500 FC (standard in Kinshasa)
        rounded_price = round(estimated_price_fc / 500) * 500

        return {
            "distance_km": round(distance_km, 2),
            "estimated_price_fc": max(2000, int(rounded_price)), # Min fare 2000 FC
            "currency": "FC"
        }

    @staticmethod
    def request_ride(client, pickup_address, pickup_lat, pickup_lng, dropoff_address, dropoff_lat, dropoff_lng, agreed_price):
        """
        Creates a Ride request from the mobile application.
        """
        ride = Ride.objects.create(
            client=client,
            status=Ride.Status.REQUESTED,
            pickup_address=pickup_address,
            pickup_latitude=pickup_lat,
            pickup_longitude=pickup_lng,
            dropoff_address=dropoff_address,
            dropoff_latitude=dropoff_lat,
            dropoff_longitude=dropoff_lng,
            agreed_price=agreed_price
        )
        logger.info(f"Ride request #{ride.id} created by client {client.phone_number}")
        return ride
