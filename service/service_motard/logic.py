import logging
from django.utils import timezone
from apps.fleet.models import Motorcycle
from apps.geoloc.models import LocationPing

logger = logging.getLogger(__name__)

class MotardHardwareService:
    """
    Service managing data coming from motorcycle GPS trackers.
    """
    
    # Simulation of a Redis client for the purpose of this implementation.
    # In production, this would be: import redis; redis_client = redis.Redis(...)
    _redis_mock = {}

    @classmethod
    def process_ping(cls, device_id, latitude, longitude, speed=None, battery=None):
        """
        Process a GPS ping from a hardware tracker.
        """
        try:
            # 1. Identify the motorcycle linked to this IMEI
            motorcycle = Motorcycle.objects.get(device_id=device_id)
            
            # 2. Update "Hot Data" in Redis for real-time tracking
            # Key: motard_pos:{motorcycle_id} -> Value: {lat, lng, speed, battery, timestamp}
            cls._update_redis_position(motorcycle.id, latitude, longitude, speed, battery)
            
            # 3. Periodic Archive to PostgreSQL (Cold Data)
            # To avoid overloading DB, we only save a ping every X minutes or on significant movement.
            cls._archive_position(motorcycle, latitude, longitude)
            
            return {
                "status": "success",
                "motorcycle_id": motorcycle.id,
                "motard": motorcycle.assigned_motard.get_full_name() if motorcycle.assigned_motard else "Non assignée"
            }
            
        except Motorcycle.DoesNotExist:
            logger.error(f"Unknown device_id received: {device_id}")
            return {"status": "error", "message": "Unknown device"}
        except Exception as e:
            logger.exception(f"Error processing ping for {device_id}: {e}")
            return {"status": "error", "message": str(e)}

    @classmethod
    def _update_redis_position(cls, moto_id, lat, lng, speed, battery):
        """
        Updates the latest position in Redis for ultra-fast access by the dashboard.
        """
        data = {
            "lat": lat,
            "lng": lng,
            "speed": speed,
            "battery": battery,
            "timestamp": timezone.now().isoformat()
        }
        cls._redis_mock[f"moto_pos:{moto_id}"] = data
        # In reality: redis_client.set(f"moto_pos:{moto_id}", json.dumps(data))
        logger.debug(f"Redis updated for moto {moto_id}: {lat}, {lng}")

    @classmethod
    def _archive_position(cls, motorcycle, lat, lng):
        """
        Saves the position to PostgreSQL for history/audit.
        """
        if motorcycle.assigned_motard:
            LocationPing.objects.create(
                user=motorcycle.assigned_motard,
                latitude=lat,
                longitude=lng
            )
