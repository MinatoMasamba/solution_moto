from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase

from apps.users.models import MotardProfile, User
from apps.rides.models import Ride, RideRating
from apps.rides.services import (
    accept_ride,
    cancel_ride,
    complete_ride,
    create_ride_request,
    start_ride,
)


def make_client(phone="+243810000001", name="Sarah"):
    return User.objects.create_user(phone, "pw", role=User.Role.CLIENT, first_name=name)


def make_motard(phone="+243810000002", name="Jean", status=None, approved=True, available=True):
    motard = User.objects.create_user(phone, "pw", role=User.Role.MOTARD, first_name=name)
    MotardProfile.objects.get_or_create(
        user=motard,
        defaults={
            "subscription_status": status or MotardProfile.SubscriptionStatus.ACTIVE,
            "application_status": (
                MotardProfile.ApplicationStatus.APPROVED if approved else MotardProfile.ApplicationStatus.PENDING
            ),
            "is_available": available,
        },
    )
    return motard


class CreateRideRequestTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_only_client_can_request(self):
        motard = make_motard()
        with self.assertRaises(Exception):
            create_ride_request(motard, pickup_address="A", dropoff_address="B")

    def test_single_active_ride(self):
        client = make_client()
        create_ride_request(client, pickup_address="A", dropoff_address="B")
        with self.assertRaises(Exception):
            create_ride_request(client, pickup_address="A", dropoff_address="B")

    def test_notifies_eligible_motards_only(self):
        make_motard("+243810000003", available=True)  # éligible
        make_motard("+243810000004", available=False)  # pas dispo
        make_motard("+243810000005", status=MotardProfile.SubscriptionStatus.EXPIRED)  # abonnement inactif
        client = make_client()
        create_ride_request(client, pickup_address="Gombe", dropoff_address="Limete", agreed_price=Decimal("1000"))
        from apps.users.models import Notification

        notified = Notification.objects.filter(kind="ride").count()
        self.assertEqual(notified, 1)
        self.assertTrue(
            Notification.objects.filter(body__contains="Gombe → Limete").exists()
        )


class RideLifecycleTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client_user = make_client()
        self.motard = make_motard()
        self.ride = create_ride_request(self.client_user, pickup_address="A", dropoff_address="B")

    def test_full_lifecycle(self):
        accept_ride(self.ride, self.motard)
        self.assertEqual(self.ride.status, Ride.Status.ACCEPTED)
        self.assertEqual(self.ride.motard, self.motard)

        start_ride(self.ride)
        self.assertEqual(self.ride.status, Ride.Status.ONGOING)

        complete_ride(self.ride, agreed_price=Decimal("1500"))
        self.assertEqual(self.ride.status, Ride.Status.COMPLETED)

    def test_accept_twice_fails(self):
        accept_ride(self.ride, self.motard)
        with self.assertRaises(Exception):
            accept_ride(self.ride, self.motard)

    def test_accept_requires_active_subscription(self):
        profile = self.motard.motard_profile
        profile.subscription_status = MotardProfile.SubscriptionStatus.EXPIRED
        profile.save()
        with self.assertRaises(Exception):
            accept_ride(self.ride, self.motard)

    def test_accept_requires_approved_application(self):
        profile = self.motard.motard_profile
        profile.application_status = MotardProfile.ApplicationStatus.PENDING
        profile.save()
        with self.assertRaises(Exception):
            accept_ride(self.ride, self.motard)
        self.assertEqual(self.ride.status, Ride.Status.REQUESTED)

    def test_cancel_notifies_parties(self):
        from apps.users.models import Notification

        accept_ride(self.ride, self.motard)
        cancel_ride(self.ride)
        self.assertEqual(self.ride.status, Ride.Status.CANCELLED)
        # client + motard notifiés de l'annulation
        self.assertTrue(Notification.objects.filter(user=self.client_user, title="Course annulée").exists())
        self.assertTrue(Notification.objects.filter(user=self.motard, title="Course annulée").exists())

    def test_status_changes_notify_client(self):
        from apps.users.models import Notification

        accept_ride(self.ride, self.motard)
        self.assertTrue(Notification.objects.filter(user=self.client_user, title="Course acceptée").exists())
        start_ride(self.ride)
        self.assertTrue(Notification.objects.filter(user=self.client_user, title="Course démarrée").exists())
        complete_ride(self.ride)
        self.assertTrue(Notification.objects.filter(user=self.client_user, title="Course terminée").exists())


class RideRatingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client_user = make_client()
        self.motard = make_motard()
        self.ride = create_ride_request(self.client_user, pickup_address="A", dropoff_address="B")

    def test_rating_scope(self):
        from django.test import Client

        accept_ride(self.ride, self.motard)
        start_ride(self.ride)
        complete_ride(self.ride)
        c = Client()
        c.force_login(self.client_user)
        r = c.post(
            "/api/v1/ride-ratings/",
            data={"ride": self.ride.pk, "score": 5, "comment": "Top"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(RideRating.objects.count(), 1)
        r2 = c.get("/api/v1/ride-ratings/")
        self.assertEqual(r2.status_code, 200)
