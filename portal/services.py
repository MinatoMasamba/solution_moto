from datetime import timedelta

from django.db.models import Sum, Count, Avg, F, Value, FloatField
from django.db.models.functions import Cast, TruncHour, TruncDate
from django.utils import timezone
from django.db.models import Q
from apps.rides.models import Ride, RideRating, RideRating
from apps.users.models import User, MotardProfile, SupportTicket
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
            "total_ratings": RideRating.objects.count(),
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
                # Pas de champ commune dans le modèle : on n'invente pas de donnée.
                "commune": None,
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
    def get_motard_kpis(motard):
        """KPIs for the Chauffeur (motard) app — scoped to the logged-in motard."""
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())

        rides = Ride.objects.filter(motard=motard)
        completed = rides.filter(status=Ride.Status.COMPLETED)

        today_qs = completed.filter(completed_at__date=today)
        week_qs = completed.filter(completed_at__date__gte=week_start)

        today_earnings = today_qs.aggregate(total=Sum("agreed_price"))["total"] or 0
        week_earnings = week_qs.aggregate(total=Sum("agreed_price"))["total"] or 0

        profile = MotardProfile.objects.filter(user=motard).first()

        return {
            "today_earnings": today_earnings,
            "today_rides": today_qs.count(),
            "week_earnings": week_earnings,
            "week_rides": week_qs.count(),
            "total_rides": completed.count(),
            "rating": float(profile.rating_average) if profile else 0.0,
            "subscription_status": profile.subscription_status if profile else "expired",
            "is_available": bool(profile.is_available) if profile else False,
            "has_open_request": rides.filter(status=Ride.Status.REQUESTED).exists()
            or Ride.objects.filter(status=Ride.Status.REQUESTED).exists(),
        }

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

        supervised = User.objects.filter(assigned_motorcycle__in=bikes).distinct()
        today_rides = Ride.objects.filter(
            motard__in=supervised, requested_at__date=today
        ).count()
        online_motards = MotardProfile.objects.filter(
            user__in=supervised, is_available=True
        ).count()
        avg_rating = MotardProfile.objects.filter(user__in=supervised).aggregate(
            avg=Avg("rating_average")
        )["avg"] or 0

        return {
            "total_bikes": total_bikes,
            "bikes_in_maintenance": bikes_in_maintenance,
            "motards_supervised": motards_supervised,
            "ongoing_trials": ongoing_trials,
            "today_revenue": today_revenue,
            "incomplete_trial_payments": incomplete_trial_payments,
            "today_rides": today_rides,
            "online_motards": online_motards,
            "avg_rating": float(avg_rating),
        }

    @staticmethod
    def get_manager_watchlist(fleet_manager=None, limit=5):
        """Motards à suivre : hors ligne, note en baisse ou abonnement expiré."""
        bikes = Motorcycle.objects.filter(fleet_manager__isnull=False)
        if fleet_manager is not None:
            bikes = bikes.filter(fleet_manager=fleet_manager)
        profiles = MotardProfile.objects.filter(
            user__assigned_motorcycle__in=bikes
        ).select_related("user").distinct()

        watch = []
        for p in profiles:
            name = p.user.get_full_name() or p.user.phone_number
            if p.subscription_status == "expired":
                watch.append({"name": name, "reason": "Abonnement expiré", "action": "relancer"})
            elif not p.is_available:
                watch.append({"name": name, "reason": "Hors ligne", "action": "à appeler"})
            elif p.rating_average is not None and float(p.rating_average) < 4.2:
                watch.append({
                    "name": name,
                    "reason": "Note en baisse · ★ " + str(p.rating_average).replace(".", ","),
                    "action": "à suivre",
                })
        return watch[:limit]

    @staticmethod
    def get_manager_remittances(fleet_manager=None):
        """Synthèse reversements : à envoyer (calculé sur les courses de la semaine),
        déjà envoyé (reversements enregistrés sur 7 jours), propriétaires en attente."""
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        bikes = Motorcycle.objects.filter(
            fleet_manager__isnull=False,
            ownership_type=Motorcycle.OwnershipType.OWNER_FLEET,
        ).select_related("owner")
        if fleet_manager is not None:
            bikes = bikes.filter(fleet_manager=fleet_manager)

        to_send = 0
        pending_owners = set()
        for bike in bikes:
            if bike.assigned_motard is None:
                continue
            gross = Ride.objects.filter(
                motard=bike.assigned_motard,
                status=Ride.Status.COMPLETED,
                requested_at__date__gte=week_start,
            ).aggregate(total=Sum("agreed_price"))["total"] or 0
            net = gross - (gross * bike.commission_rate) / 100
            if net > 0:
                to_send += net
                if bike.owner_id:
                    pending_owners.add(bike.owner_id)

        from apps.fleet.models import FleetRemittance
        sent_week = FleetRemittance.objects.filter(
            motorcycle__in=bikes,
            created_at__date__gte=today - timedelta(days=7),
        ).aggregate(total=Sum("net_amount"))["total"] or 0

        return {
            "to_send": to_send,
            "sent_week": sent_week,
            "pending_owners": len(pending_owners),
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
    def get_support_requests(limit=30):
        """Tickets support réels créés par les utilisateurs (modèle SupportTicket)."""
        tickets = SupportTicket.objects.select_related("requester").order_by(
            "-created_at"
        )[:limit]
        items = [
            {
                "id": t.id,
                "requester": t.requester.get_full_name() or t.requester.phone_number,
                "role": t.requester.get_role_display(),
                "subject": t.subject,
                "priority": t.priority,
                "priority_label": t.get_priority_display(),
                "status": t.status,
                "status_label": t.get_status_display(),
                "date": t.created_at.strftime("%d/%m/%Y"),
            }
            for t in tickets
        ]
        open_count = SupportTicket.objects.filter(
            status=SupportTicket.Status.OPEN
        ).count()
        return {"open": open_count, "items": items}

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

        total_clients = base.count()
        new_today = base.filter(date_joined__date=timezone.localdate()).count()
        total_client_rides = Ride.objects.filter(client__role=User.Role.CLIENT).count()
        avg_rides = round(total_client_rides / total_clients, 1) if total_clients else 0
        avg_rating = RideRating.objects.filter(
            rated_by__role=User.Role.CLIENT
        ).aggregate(avg=Avg("score"))["avg"] or 0

        return {
            "total": total_clients,
            "new_today": new_today,
            "avg_rides": avg_rides,
            "rating": round(float(avg_rating), 1),
            "clients": results,
        }

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

        day_names = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        days = [
            {
                "date": f"{day_names[d.weekday()]} {d.day:02d}",
                "count": v["count"],
                "revenue": v["revenue"],
            }
            for d, v in sorted(by_day.items())
        ]
        return {
            "days": days,
            "total_revenue": sum(d["revenue"] for d in days),
            "total_rides": sum(d["count"] for d in days),
        }
