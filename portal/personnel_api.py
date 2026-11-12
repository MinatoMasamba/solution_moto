"""Authenticated DG snapshot. Every displayed row originates in persisted models."""
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from apps.users.models import User, MotardProfile, SupportTicket, Notification
from apps.fleet.models import Motorcycle, FleetRemittance
from apps.rides.models import Ride
from apps.geoloc.services import latest_positions_for
from apps.geoloc.simulation import snapshot, advance
from apps.geoloc.models import SimulationRun
from django.db import transaction
from .views import IsOperator
from .services import DashboardService


def identity(u):
    return {'id':u.pk,'name':u.get_full_name() or u.phone_number,'phone':u.phone_number,'email':u.email,'role':u.get_role_display(),'first_name':u.first_name,'last_name':u.last_name}


class PersonnelSnapshot(APIView):
    permission_classes = [IsOperator]

    def get(self, request):
        today=timezone.localdate()
        rows=[]
        for p in MotardProfile.objects.select_related('user').order_by('pk'):
            rides=Ride.objects.filter(motard=p.user,requested_at__date=today,status='completed')
            row=identity(p.user)
            row.update(profile_id=p.pk,commune=p.commune,status=p.get_application_status_display(),application_status=p.application_status,subscription=p.get_subscription_status_display(),available=p.is_available,rating=str(p.rating_average),rides=rides.count(),revenue=rides.aggregate(v=Sum('agreed_price'))['v'] or 0,license=p.license_number,identity=p.id_card_number,document=p.photo_piece_identite.url if p.photo_piece_identite else None)
            rows.append(row)
        clients=[]
        for u in User.objects.filter(role='client'):
            r=Ride.objects.filter(client=u)
            clients.append(dict(identity(u),rides=r.count(),spent=r.filter(status='completed').aggregate(v=Sum('agreed_price'))['v'] or 0,joined=u.date_joined))
        managers=[]
        for u in User.objects.filter(role='fleet_manager'):
            bikes=Motorcycle.objects.filter(fleet_manager=u)
            managers.append(dict(identity(u),motorcycles=bikes.count(),assigned=bikes.filter(status='assigned').count(),maintenance=bikes.filter(status='maintenance').count()))
        commissions=[{'id':r.pk,'plate':r.motorcycle.plate_number,'owner':r.motorcycle.owner.get_full_name() if r.motorcycle.owner else 'GO-MBOKA','start':r.period_start,'end':r.period_end,'gross':r.gross_revenue,'commission':r.commission_amount,'net':r.net_amount} for r in FleetRemittance.objects.select_related('motorcycle__owner').order_by('-created_at')]
        notices=[{'id':n.pk,'title':n.title,'body':n.body,'kind':n.get_kind_display(),'read':bool(n.read_at),'date':n.created_at} for n in Notification.objects.filter(user=request.user)]
        tickets=[{'id':t.pk,'name':t.requester.get_full_name() or t.requester.phone_number,'subject':t.subject,'message':t.message,'priority':t.get_priority_display(),'status':t.status,'status_label':t.get_status_display(),'date':t.created_at} for t in SupportTicket.objects.select_related('requester')]
        return Response({'me':identity(request.user),'kpis':DashboardService.get_operator_kpis(),'activity':DashboardService.get_hourly_activity(),'motards':rows,'clients':clients,'managers':managers,'commissions':commissions,'notifications':notices,'support':tickets,'positions':latest_positions_for(request.user),'simulation':snapshot(),'updated_at':timezone.now()})

    def post(self, request):
        action=request.data.get('action')
        if action in ('simulation_pause','simulation_resume','simulation_step'):
            with transaction.atomic():
                run=get_object_or_404(SimulationRun.objects.select_for_update(),pk=request.data.get('id'))
                if run.status=='completed': raise ValidationError('Trajet terminé. Créer une nouvelle simulation.')
                run.status='paused' if action=='simulation_pause' else 'running'
                run.save(update_fields=['status','updated_at'])
                if action=='simulation_step':
                    run=advance(run.pk,10)
                    if run.status!='completed':
                        run.status='paused';run.save(update_fields=['status','updated_at'])
        elif action=='notification_read':
            n=get_object_or_404(Notification,user=request.user,pk=request.data.get('id'))
            n.read_at=timezone.now();n.save(update_fields=['read_at'])
        elif action=='support_status':
            status=request.data.get('status')
            if status not in SupportTicket.Status.values: raise ValidationError('Statut invalide.')
            t=get_object_or_404(SupportTicket,pk=request.data.get('id'))
            t.status=status;t.resolved_at=timezone.now() if status=='resolved' else None
            t.save(update_fields=['status','resolved_at'])
        elif action=='application':
            status=request.data.get('status')
            if status not in ('approved','rejected'): raise ValidationError('Décision invalide.')
            p=get_object_or_404(MotardProfile,pk=request.data.get('id'))
            p.application_status=status;p.save(update_fields=['application_status'])
            Notification.objects.create(user=p.user,kind='system',title='Décision sur votre dossier',body=p.get_application_status_display())
        else: raise ValidationError('Action inconnue.')
        return Response({'ok':True})
