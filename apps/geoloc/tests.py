from django.test import Client, TestCase

from apps.users.models import MotardProfile, User
from apps.geoloc.services import record_ping


class LocationPingAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.motard = User.objects.create_user("+243830000001", "pw", role=User.Role.MOTARD)
        MotardProfile.objects.create(
            user=self.motard,
            subscription_status=MotardProfile.SubscriptionStatus.ACTIVE,
            application_status=MotardProfile.ApplicationStatus.APPROVED,
            is_available=True,
        )
        self.client_user = User.objects.create_user("+243830000002", "pw", role=User.Role.CLIENT)
        self.other = User.objects.create_user("+243830000003", "pw", role=User.Role.CLIENT)

    def _current_ride(self):
        from apps.rides.models import Ride
        from apps.rides.services import accept_ride, create_ride_request

        ride = create_ride_request(self.client_user, pickup_address="A", dropoff_address="B")
        return accept_ride(ride, self.motard)

    def test_client_reads_motard_pings_of_his_ride(self):
        ride = self._current_ride()
        record_ping(self.motard, -4.32, 15.30, ride=ride)
        record_ping(self.motard, -4.33, 15.31, ride=ride)

        c = Client()
        c.force_login(self.client_user)
        r = c.get(f"/api/v1/location-pings/?ride={ride.pk}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["count"], 2)

    def test_client_cannot_read_foreign_pings(self):
        ride = self._current_ride()
        record_ping(self.motard, -4.32, 15.30, ride=ride)

        c = Client()
        c.force_login(self.other)
        r = c.get(f"/api/v1/location-pings/?ride={ride.pk}")
        self.assertEqual(r.json()["count"], 0)

    def test_current_includes_motard_position(self):
        ride = self._current_ride()
        record_ping(self.motard, -4.32, 15.30, ride=ride)

        c = Client()
        c.force_login(self.client_user)
        r = c.get("/api/v1/rides/current/")
        self.assertEqual(r.status_code, 200)
        pos = r.json()["ride"]["motard_position"]
        self.assertIsNotNone(pos)
        self.assertEqual(pos["latitude"], -4.32)

    def test_motard_can_ping(self):
        c = Client()
        c.force_login(self.motard)
        r = c.post(
            "/api/v1/location-pings/",
            data={"latitude": -4.32, "longitude": 15.30},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 201)
