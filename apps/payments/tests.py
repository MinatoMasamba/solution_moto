from decimal import Decimal

from django.core.cache import cache
from django.test import Client, TestCase

from apps.users.models import MotardProfile, Notification, User


class ProviderSimulatorTests(TestCase):
    def test_initiate_charge_auto_success(self):
        from apps.payments.providers.simulator import SimulatorProvider

        result = SimulatorProvider().initiate_charge(amount=Decimal("1000"), phone_number="+243900000000")
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["provider_reference"].startswith("sim-"))

    def test_unknown_provider_raises(self):
        from django.test import override_settings

        from apps.payments.providers import PaymentProviderError, get_provider

        with override_settings(PAYMENT_PROVIDER="inconnu"):
            with self.assertRaises(PaymentProviderError):
                get_provider()


class WalletTopupTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user("+243900000001", "pw", role=User.Role.CLIENT, first_name="Sarah")
        self.client.force_login(self.user)

    def test_topup_auto_success(self):
        r = self.client.post("/api/v1/wallet/", data={"amount": "5000", "provider": "mpesa"}, content_type="application/json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["transaction"]["status"], "success")
        self.assertEqual(Decimal(str(r.json()["balance"])), Decimal("5000"))

    def test_topup_invalid_amount(self):
        r = self.client.post("/api/v1/wallet/", data={"amount": "-5"}, content_type="application/json")
        self.assertEqual(r.status_code, 400)


class WalletWebhookTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.user = User.objects.create_user("+243900000002", "pw", role=User.Role.CLIENT)
        self.txn = self.user.wallet_transactions.create(
            kind="topup", amount=Decimal("1000"), status="pending"
        )

    def test_webhook_requires_token(self):
        r = self.client.post("/api/v1/payments/webhook/", data={"reference": self.txn.pk}, content_type="application/json")
        self.assertEqual(r.status_code, 403)

    def test_webhook_confirms_pending(self):
        r = self.client.post(
            "/api/v1/payments/webhook/?token=dev-webhook-token",
            data={"reference": self.txn.pk, "status": "success"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.status, "success")

    def test_webhook_fails_txn(self):
        r = self.client.post(
            "/api/v1/payments/webhook/?token=dev-webhook-token",
            data={"reference": self.txn.pk, "status": "failed"},
            content_type="application/json",
        )
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.status, "failed")

    def test_webhook_unknown_txn(self):
        r = self.client.post(
            "/api/v1/payments/webhook/?token=dev-webhook-token",
            data={"reference": 999999, "status": "success"},
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 404)


class WalletDebitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("+243900000003", "pw", role=User.Role.CLIENT, first_name="Lili")

    def _ride(self, price, status="ongoing"):
        from apps.rides.models import Ride

        return Ride.objects.create(
            client=self.user, status=status,
            pickup_address="Gombe", pickup_latitude=0, pickup_longitude=0,
            dropoff_address="Ngaliema", dropoff_latitude=0, dropoff_longitude=0,
            agreed_price=price,
        )

    def test_debit_on_completion(self):
        from apps.rides.services import complete_ride

        self.user.wallet_transactions.create(kind="topup", amount=Decimal("5000"), status="success")
        ride = self._ride(Decimal("2000"))
        complete_ride(ride)
        txn = self.user.wallet_transactions.filter(kind="ride").first()
        self.assertIsNotNone(txn)
        self.assertEqual(txn.amount, Decimal("-2000"))

    def test_insufficient_balance_no_debit(self):
        from apps.rides.services import complete_ride

        self.user.wallet_transactions.create(kind="topup", amount=Decimal("100"), status="success")
        ride = self._ride(Decimal("2000"))
        complete_ride(ride)
        self.assertFalse(self.user.wallet_transactions.filter(kind="ride").exists())

    def test_no_price_no_debit(self):
        from apps.rides.services import complete_ride

        ride = self._ride(None)
        complete_ride(ride)
        self.assertFalse(self.user.wallet_transactions.filter(kind="ride").exists())


class SubscriptionPayTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()
        self.motard = User.objects.create_user("+243900000004", "pw", role=User.Role.MOTARD, first_name="Jean")
        MotardProfile.objects.create(user=self.motard)
        self.client.force_login(self.motard)

    def test_price_endpoint(self):
        r = self.client.get("/api/v1/subscriptions/price/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("amount", r.json())

    def test_pay_activates_subscription(self):
        r = self.client.post("/api/v1/subscriptions/", data={"amount": "15000"}, content_type="application/json")
        self.assertEqual(r.status_code, 201)
        sub_id = r.json()["id"]

        r = self.client.post(f"/api/v1/subscriptions/{sub_id}/pay/", data={}, content_type="application/json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["payment"]["status"], "success")
        self.assertEqual(r.json()["subscription"]["status"], "active")

        profile = MotardProfile.objects.get(user=self.motard)
        self.assertEqual(profile.subscription_status, MotardProfile.SubscriptionStatus.ACTIVE)
        self.assertTrue(self.motard.notifications.filter(kind="subscription").exists())

    def test_pay_other_subscription_forbidden(self):
        other = User.objects.create_user("+243900000005", "pw", role=User.Role.MOTARD)
        sub = Subscription.objects.create(motard=other, amount=Decimal("15000"))
        r = self.client.post(f"/api/v1/subscriptions/{sub.pk}/pay/", data={}, content_type="application/json")
        # get_object() est scopé sur le queryset (motard=user) -> 404
        self.assertEqual(r.status_code, 404)


from apps.payments.models import Subscription  # noqa: E402  (placé ici pour lisibilité du test ci-dessus)
