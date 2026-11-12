from django.core.cache import cache
from django.test import Client, TestCase

from apps.users.models import MotardProfile, Notification, User
from apps.users.services import expire_outdated_subscriptions
from service.service_rides.logic import RideDispatchService


def make_motard(phone, *, sub="active", approved=True, available=True, expires=None):
    user = User.objects.create_user(phone, "pw", role=User.Role.MOTARD)
    MotardProfile.objects.get_or_create(
        user=user,
        defaults={
            "subscription_status": sub,
            "application_status": (
                MotardProfile.ApplicationStatus.APPROVED if approved else MotardProfile.ApplicationStatus.PENDING
            ),
            "is_available": available,
            "subscription_expires_at": expires,
        },
    )
    return user


class DispatchEligibilityTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_only_active_approved_available(self):
        make_motard("+243820000001")  # OK
        make_motard("+243820000002", sub="expired")
        make_motard("+243820000003", approved=False)
        make_motard("+243820000004", available=False)
        eligible = RideDispatchService.filter_eligible_motards_for_dispatch(User.objects.all())
        self.assertEqual(eligible.count(), 1)
        self.assertEqual(eligible.first().phone_number, "+243820000001")

    def test_non_motard_never_eligible(self):
        client = User.objects.create_user("+243820000005", "pw", role=User.Role.CLIENT)
        self.assertFalse(RideDispatchService.is_motard_eligible_for_requests(client))


class SubscriptionExpiryTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_expire_outdated_subscriptions(self):
        from django.utils import timezone

        past = timezone.now() - timezone.timedelta(days=1)
        m = make_motard("+243820000011", expires=past)
        profile = m.motard_profile
        self.assertEqual(profile.subscription_status, "active")

        count = expire_outdated_subscriptions()
        self.assertEqual(count, 1)
        profile.refresh_from_db()
        self.assertEqual(profile.subscription_status, "expired")

    def test_lazy_expiry_blocks_accept(self):
        from django.utils import timezone

        from apps.rides.models import Ride
        from apps.rides.services import accept_ride

        past = timezone.now() - timezone.timedelta(days=1)
        motard = make_motard("+243820000012", expires=past)
        client = User.objects.create_user("+243820000013", "pw", role=User.Role.CLIENT)
        ride = Ride.objects.create(
            client=client, status=Ride.Status.REQUESTED,
            pickup_address="A", pickup_latitude=0, pickup_longitude=0,
            dropoff_address="B", dropoff_latitude=0, dropoff_longitude=0,
        )
        with self.assertRaises(Exception):
            accept_ride(ride, motard)
        self.assertEqual(ride.status, Ride.Status.REQUESTED)


class NotificationsAPITests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user("+243820000021", "pw", role=User.Role.CLIENT)
        self.client.force_login(self.user)
        Notification.objects.create(user=self.user, kind="ride", title="T1")
        Notification.objects.create(user=self.user, kind="payment", title="T2")

    def test_list_with_unread_count(self):
        r = self.client.get("/api/v1/notifications/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["unread"], 2)
        self.assertEqual(len(data["items"]), 2)

    def test_mark_all_read(self):
        r = self.client.post("/api/v1/notifications/", data={}, content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["unread"], 0)

    def test_requires_auth(self):
        c = Client()
        r = c.get("/api/v1/notifications/")
        self.assertEqual(r.status_code, 401)


class PasswordResetRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("+243820000031", "pw", role=User.Role.CLIENT)
        self.user.email = "reset@test.cd"
        self.user.save()
        self.c = Client()

    def test_request_limit(self):
        payload = '{"email":"reset@test.cd"}'
        statuses = [
            self.c.post("/chauffeur/mot-de-passe/demande/", data=payload, content_type="application/json").status_code
            for _ in range(4)
        ]
        self.assertEqual(statuses[:3], [200, 200, 200])
        self.assertEqual(statuses[3], 429)

    def test_attempt_limit_invalidates_code(self):
        from django.core.cache import cache

        self.c.post("/chauffeur/mot-de-passe/demande/", data='{"email":"reset@test.cd"}', content_type="application/json")
        code = cache.get("chauffeur-password-reset:reset@test.cd")
        self.assertIsNotNone(code)
        bad = '{"email":"reset@test.cd","code":"000000","password":"Nouveau123","password2":"Nouveau123"}'
        for _ in range(5):
            r = self.c.post("/chauffeur/mot-de-passe/confirmation/", data=bad, content_type="application/json")
            self.assertEqual(r.status_code, 400)
        # 6e tentative avec le BON code : le code a été invalidé après 5 essais
        good = '{"email":"reset@test.cd","code":"%s","password":"Nouveau123","password2":"Nouveau123"}' % code
        r = self.c.post("/chauffeur/mot-de-passe/confirmation/", data=good, content_type="application/json")
        self.assertEqual(r.status_code, 429)
