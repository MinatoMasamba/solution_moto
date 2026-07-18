from datetime import timedelta

from django.db.models import Sum, Count, Avg, F, Value, FloatField
from django.db.models.functions import Cast, TruncHour, TruncDate
from django.utils import timezone
from django.db.models import Q
from apps.rides.models import Ride
from apps.users.models import User, MotardProfile
from apps.fleet.models import MotardTrial, Motorcycle, TrialDailyLog
from apps.payments.models import Payment, Subscription

class DashboardService:
    """
    Service to aggregate data for the Operator and Owner dashboards.
    """

    @staticmethod
    def get_operator_kpis():
        today = timezone.now().date()
        rides_today = Ride.objects.filter(requested_at__date=today)
        
        total_rides = rides_today.count()
        
        # Motards active vs total
        total_motards = User.objects.filter(role=User.Role.MOTARD).count()
        active_motards = MotardProfile.objects.filter(
            user__role=User.Role.MOTARD, 
            is_available=True
        ).count()
        
        # Revenue today (FC)
        total_revenue_fc = rides_today.filter(status=Ride.Status.COMPLETED).aggregate(
            total=Sum('agreed_price')
        )['total'] or 0
        
        # Estimated USD (assuming 1 USD = 2850 FC)
        total_revenue_usd = total_revenue_fc / 2850
        
        # Average Rating
        avg_rating = MotardProfile.objects.aggregate(
            avg=Avg('rating_average')
        )['avg'] or 0
        
        return {
            "total_rides": total_rides,
            "active_motards": active_motards,
            "total_motards": total_motards,
            "revenue_fc": total_revenue_fc,
            "revenue_usd": total_revenue_usd,
            "avg_rating": float(avg_rating),
        }

    @staticmethod
    def get_hourly_activity():
        today = timezone.now().date()
        rides_today = Ride.objects.filter(requested_at__date=today)
        
        # Group by hour for rides count and revenue
        activity = rides_today.annotate(
            hour=TruncHour('requested_at')
        ).values('hour').annotate(
            count=Count('id'),
            revenue=Sum('agreed_price')
        ).order_by('hour')
        
        # Fill gaps for all 24 hours
        full_day = {h: {"count": 0, "revenue": 0} for h in range(24)}
        for item in activity:
            hour = item['hour'].hour
            full_day[hour] = {"count": item['count'], "revenue": item['revenue'] or 0}
            
        return full_day

    @staticmethod
    def get_top_motards(limit=5):
        today = timezone.now().date()
        # Get motards with the most completed rides today
        top_motards = User.objects.filter(
            role=User.Role.MOTARD,
            rides_as_motard__requested_at__date=today,
            rides_as_motard__status=Ride.Status.COMPLETED
        ).annotate(
            ride_count=Count('rides_as_motard'),
            total_revenue=Sum('rides_as_motard__agreed_price')
        ).order_by('-ride_count', '-total_revenue')[:limit]
        
        results = []
        for m in top_motards:
            profile = getattr(m, 'motard_profile', None)
            # Find which pillar they belong to via their assigned motorcycle
            pillar = "Abonnement"
            try:
                moto = m.assigned_motorcycle
                if moto.ownership_type == Motorcycle.OwnershipType.OWNER_FLEET:
                    pillar = f"Gérance · {moto.owner.get_full_name() if moto.owner else 'Inconnu'}"
                elif moto.ownership_type == Motorcycle.OwnershipType.PLATFORM_FLEET:
                    pillar = "Allocation moto"
            except AttributeError:
                pass
                
            results.append({
                "name": m.get_full_name(),
                "commune": "Gombe", # Placeholder: we'll need a Commune model/field later
                "rides": m.ride_count,
                "revenue": m.total_revenue or 0,
                "rating": profile.rating_average if profile else 0,
                "pillar": pillar
            })
        return results

    @staticmethod
    def get_owner_kpis(owner=None):
        """KPIs for the Owner (propriétaire) dashboard.

        Pass `owner` to scope every figure to a single logged-in owner;
        omit it (operator/staff view) to get platform-wide totals.
        """
        bikes = Motorcycle.objects.filter(ownership_type=Motorcycle.OwnershipType.OWNER_FLEET)
        if owner is not None:
            bikes = bikes.filter(owner=owner)

        total_fleets = 1 if owner is not None else User.objects.filter(role=User.Role.OWNER).count()
        total_bikes = bikes.count()

        motards_in_fleet = User.objects.filter(assigned_motorcycle__in=bikes)
        active_motards = MotardProfile.objects.filter(
            user__in=motards_in_fleet, is_available=True
        ).count()

        now = timezone.now()
        paid_subs = Subscription.objects.filter(
            motard__in=motards_in_fleet,
            status=Subscription.Status.ACTIVE,
            period_end__gte=now,
        ).count()

        open_alerts = Payment.objects.filter(
            user__in=motards_in_fleet, status__in=[Payment.Status.FAILED, Payment.Status.PENDING]
        ).count()

        return {
            "total_fleets": total_fleets,
            "total_bikes": total_bikes,
            "active_motards": active_motards,
            "paid_subscriptions": paid_subs,
            "open_alerts": open_alerts,
        }

    @staticmethod
    def get_fleet_commissions(owner=None):
        today = timezone.now().date()
        owners = User.objects.filter(role=User.Role.OWNER)
        if owner is not None:
            owners = owners.filter(pk=owner.pk)
        fleet_data = []

        for o in owners:
            bikes = Motorcycle.objects.filter(owner=o, ownership_type=Motorcycle.OwnershipType.OWNER_FLEET)
            bike_count = bikes.count()
            if bike_count == 0: continue

            # Calculate revenue for these bikes today
            # We find rides completed by motards assigned to these bikes
            motards_in_fleet = User.objects.filter(assigned_motorcycle__in=bikes)
            revenue = Ride.objects.filter(
                motard__in=motards_in_fleet,
                requested_at__date=today,
                status=Ride.Status.COMPLETED
            ).aggregate(total=Sum('agreed_price'))['total'] or 0

            # Use average commission rate of the fleet for simplification
            avg_comm = bikes.aggregate(avg=Avg('commission_rate'))['avg'] or 0
            commission_amount = (revenue * avg_comm) / 100
            net_to_remit = revenue - commission_amount

            fleet_data.append({
                "owner_name": o.get_full_name(),
                "bike_count": bike_count,
                "gross_revenue": revenue,
                "commission_rate": float(avg_comm),
                "net_to_remit": net_to_remit
            })

        return fleet_data

    @staticmethod
    def get_manager_kpis(fleet_manager=None):
        """KPIs for the Gérant de flotte (fleet manager) dashboard.

        Pass `fleet_manager` to scope to a single logged-in gérant;
        omit it (operator/staff view) to get platform-wide totals across all gérants.
        """
        today = timezone.now().date()
        bikes = Motorcycle.objects.filter(fleet_manager__isnull=False)
        if fleet_manager is not None:
            bikes = bikes.filter(fleet_manager=fleet_manager)

        total_bikes = bikes.count()
        bikes_in_maintenance = bikes.filter(status=Motorcycle.Status.MAINTENANCE).count()

        motards_supervised = User.objects.filter(assigned_motorcycle__in=bikes).distinct().count()

        ongoing_trials = MotardTrial.objects.filter(
            motorcycle__in=bikes, result=MotardTrial.TrialResult.PENDING
        ).count()

        today_revenue = Ride.objects.filter(
            motard__assigned_motorcycle__in=bikes,
            requested_at__date=today,
            status=Ride.Status.COMPLETED,
        ).aggregate(total=Sum("agreed_price"))["total"] or 0

        incomplete_trial_payments = TrialDailyLog.objects.filter(
            trial__motorcycle__in=bikes, date=today, is_payment_complete=False
        ).count()

        return {
            "total_bikes": total_bikes,
            "bikes_in_maintenance": bikes_in_maintenance,
            "motards_supervised": motards_supervised,
            "ongoing_trials": ongoing_trials,
            "today_revenue": today_revenue,
            "incomplete_trial_payments": incomplete_trial_payments,
        }

    @staticmethod
    def get_manager_fleet_detail(fleet_manager=None):
        today = timezone.now().date()
        bikes = Motorcycle.objects.select_related("owner", "assigned_motard").filter(fleet_manager__isnull=False)
        if fleet_manager is not None:
            bikes = bikes.filter(fleet_manager=fleet_manager)

        fleet_data = []
        for bike in bikes:
            revenue_today = 0
            if bike.assigned_motard is not None:
                revenue_today = Ride.objects.filter(
                    motard=bike.assigned_motard,
                    requested_at__date=today,
                    status=Ride.Status.COMPLETED,
                ).aggregate(total=Sum("agreed_price"))["total"] or 0

            fleet_data.append({
                "plate_number": bike.plate_number,
                "ownership_type": bike.ownership_type,
                "status": bike.status,
                "owner_name": bike.owner.get_full_name() if bike.owner else None,
                "motard_name": bike.assigned_motard.get_full_name() if bike.assigned_motard else None,
                "general_condition": bike.general_condition,
                "revenue_today": revenue_today,
            })
        return fleet_data

    # ──────────────────────────────────────────────────────────────────────
    # Vues secondaires — Direction Générale (opérateur)
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_operator_clients(limit=50):
        """Liste des clients avec nombre de courses et dépense totale."""
        base = User.objects.filter(role=User.Role.CLIENT)
        clients = base.annotate(
            rides_count=Count("rides_as_client"),
            total_spent=Sum(
                "rides_as_client__agreed_price",
                filter=Q(rides_as_client__status=Ride.Status.COMPLETED),
            ),
        ).order_by("-rides_count", "-date_joined")[:limit]

        results = [
            {
                "id": c.id,
                "name": c.get_full_name() or c.phone_number,
                "phone_number": c.phone_number,
                "rides": c.rides_count,
                "total_spent": c.total_spent or 0,
                "date_joined": c.date_joined.strftime("%d/%m/%Y"),
            }
            for c in clients
        ]
        return {"total": base.count(), "clients": results}

    @staticmethod
    def get_operator_gerants():
        """Liste des gérants de flotte avec la taille et le rendement de leur portefeuille."""
        today = timezone.now().date()
        results = []
        for g in User.objects.filter(role=User.Role.FLEET_MANAGER).order_by("first_name", "last_name"):
            bikes = Motorcycle.objects.filter(fleet_manager=g)
            bike_count = bikes.count()
            motards = User.objects.filter(assigned_motorcycle__in=bikes).distinct().count()
            revenue = Ride.objects.filter(
                motard__assigned_motorcycle__in=bikes,
                requested_at__date=today,
                status=Ride.Status.COMPLETED,
            ).aggregate(total=Sum("agreed_price"))["total"] or 0
            results.append({
                "id": g.id,
                "name": g.get_full_name() or g.phone_number,
                "phone_number": g.phone_number,
                "bikes": bike_count,
                "motards": motards,
                "revenue_today": revenue,
            })
        return {"total": len(results), "gerants": results}

    @staticmethod
    def get_notifications(limit=25):
        """Notifications calculées à partir d'évènements réels (aucun modèle dédié)."""
        now = timezone.now()
        today = now.date()
        items = []

        pending = MotardProfile.objects.filter(
            application_status=MotardProfile.ApplicationStatus.PENDING
        ).select_related("user")
        for p in pending[:limit]:
            items.append({
                "type": "motard_pending", "level": "warning", "icon": "ph-user-focus",
                "title": "Motard à valider",
                "detail": (p.user.get_full_name() or p.user.phone_number) + " — dossier en attente",
            })

        payments = Payment.objects.filter(
            status__in=[Payment.Status.FAILED, Payment.Status.PENDING]
        ).select_related("user")
        for pmt in payments[:limit]:
            items.append({
                "type": "payment",
                "level": "danger" if pmt.status == Payment.Status.FAILED else "info",
                "icon": "ph-coins",
                "title": "Paiement " + pmt.get_status_display().lower(),
                "detail": (pmt.user.get_full_name() or pmt.user.phone_number)
                          + " · " + str(pmt.amount) + " FC",
            })

        soon = Subscription.objects.filter(
            status=Subscription.Status.ACTIVE,
            period_end__isnull=False,
            period_end__gte=today,
            period_end__lte=today + timedelta(days=7),
        ).select_related("motard")
        for s in soon[:limit]:
            items.append({
                "type": "subscription", "level": "warning", "icon": "ph-hourglass-medium",
                "title": "Abonnement expirant",
                "detail": (s.motard.get_full_name() or s.motard.phone_number)
                          + " — échéance " + s.period_end.strftime("%d/%m"),
            })

        trial_unpaid = TrialDailyLog.objects.filter(
            date=today, is_payment_complete=False
        ).select_related("trial__motard")
        for t in trial_unpaid[:limit]:
            items.append({
                "type": "trial", "level": "danger", "icon": "ph-warning",
                "title": "Versement d'essai incomplet",
                "detail": (t.trial.motard.get_full_name() or t.trial.motard.phone_number)
                          + " — jour du " + t.date.strftime("%d/%m"),
            })

        return {"unread": len(items), "items": items[:limit]}

    # ──────────────────────────────────────────────────────────────────────
    # Vues secondaires — Gérant de flotte
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_manager_performance(fleet_manager=None):
        """Rendement des 7 derniers jours (courses + revenus) pour la flotte gérée."""
        today = timezone.now().date()
        start = today - timedelta(days=6)
        bikes = Motorcycle.objects.filter(fleet_manager__isnull=False)
        if fleet_manager is not None:
            bikes = bikes.filter(fleet_manager=fleet_manager)

        rows = Ride.objects.filter(
            motard__assigned_motorcycle__in=bikes,
            status=Ride.Status.COMPLETED,
            requested_at__date__gte=start,
            requested_at__date__lte=today,
        ).annotate(day=TruncDate("requested_at")).values("day").annotate(
            count=Count("id"), revenue=Sum("agreed_price")
        )

        by_day = {start + timedelta(days=i): {"count": 0, "revenue": 0} for i in range(7)}
        for r in rows:
            if r["day"] in by_day:
                by_day[r["day"]] = {"count": r["count"], "revenue": r["revenue"] or 0}

        days = [
            {"date": d.strftime("%a %d"), "count": v["count"], "revenue": v["revenue"]}
            for d, v in sorted(by_day.items())
        ]
        return {
            "days": days,
            "total_revenue": sum(d["revenue"] for d in days),
            "total_rides": sum(d["count"] for d in days),
        }
