"""Idempotent, additive local acceptance dataset; never overwrites an existing user."""
import secrets
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from apps.users.models import User, MotardProfile, OwnerProfile, Notification, SupportTicket
from apps.fleet.models import Motorcycle, FleetRemittance
from apps.rides.models import Ride, RideRating
from apps.geoloc.models import LocationPing
from apps.payments.models import Payment, Subscription

class Command(BaseCommand):
    help='Crée le jeu de recette personnel, sans appel Mobile Money ni message externe.'
    def add_arguments(self, parser):
        parser.add_argument('--password',required=True,help='Mot de passe des nouveaux comptes de recette uniquement.')
    @transaction.atomic
    def handle(self,*args,**opts):
        if len(opts['password'])<12: raise CommandError('12 caractères minimum.')
        now=timezone.now();today=timezone.localdate()
        def account(i,role,name):
            phone=f'+24300090{i:04}'
            u,created=User.objects.get_or_create(phone_number=phone,defaults={'role':role,'first_name':name,'last_name':'RECETTE','email':f'recette.{i}@example.invalid'})
            if u.email!=f'recette.{i}@example.invalid':raise CommandError('Collision avec un compte existant, transaction annulée.')
            if created:u.set_password(opts['password']);u.save(update_fields=['password'])
            return u
        dg=account(1,'operator','Direction');owner=account(2,'owner','Flotte');manager=account(3,'fleet_manager','Gestion')
        OwnerProfile.objects.get_or_create(user=owner,defaults={'company_name':'Flotte de recette GO-MBOKA'})
        clients=[account(20+i,'client',name) for i,name in enumerate(['Aline','Josué','Marie','Paul'])]
        for i,commune in enumerate(['Gombe','Limete','Lemba','Ngaliema','Masina','Matete']):
            u=account(10+i,'motard',['Trésor','Divine','Gédéon','Espoir','Grâce','Blaise'][i])
            p,_=MotardProfile.objects.get_or_create(user=u,defaults={'commune':commune,'ville':'Kinshasa','province':'kinshasa','license_number':f'RECETTE-P-{i}','id_card_number':f'RECETTE-ID-{i}','application_status':'pending' if i==4 else 'approved','subscription_status':'active' if i!=4 else 'expired','subscription_expires_at':now+timedelta(days=30),'is_available':i<4,'rating_average':Decimal('4.33')})
            bike,_=Motorcycle.objects.get_or_create(plate_number=f'RECETTE-KN-{i:03}',defaults={'owner':owner,'fleet_manager':manager,'assigned_motard':u,'ownership_type':'owner_fleet','brand':'TVS','model_style':'HLX 125','status':'assigned','commission_rate':10})
            Subscription.objects.get_or_create(motard=u,period_start=today,defaults={'period_end':today+timedelta(days=30),'amount':25000,'status':'active' if i!=4 else 'pending'})
            if not LocationPing.objects.filter(user=u).exists():LocationPing.objects.create(user=u,latitude=Decimal('-4.300')-Decimal(i)*Decimal('.018'),longitude=Decimal('15.290')+Decimal(i)*Decimal('.025'))
            for j in range(4):
                label=f'RECETTE {i}-{j} · {commune}'
                ride,created=Ride.objects.get_or_create(pickup_address=label,client=clients[j],defaults={'motard':u if i!=4 else None,'dropoff_address':'Marché central · Kinshasa','pickup_latitude':-4.31,'pickup_longitude':15.30,'dropoff_latitude':-4.32,'dropoff_longitude':15.32,'agreed_price':3500+j*500,'status':'completed' if j<3 and i!=4 else 'requested','accepted_at':now-timedelta(hours=2),'started_at':now-timedelta(hours=1),'completed_at':now if j<3 and i!=4 else None})
                if created:
                    started=now.replace(hour=(i+j)%max(now.hour,1),minute=10,second=0,microsecond=0)
                    Ride.objects.filter(pk=ride.pk).update(requested_at=started,accepted_at=started+timedelta(minutes=2) if ride.status=='completed' else None,started_at=started+timedelta(minutes=4) if ride.status=='completed' else None,completed_at=started+timedelta(minutes=18) if ride.status=='completed' else None)
                if created and ride.status=='completed':
                    RideRating.objects.create(ride=ride,rated_by=ride.client,score=4+j%2)
                    Payment.objects.create(user=ride.client,ride=ride,purpose='ride',provider='cash',status='success',amount=ride.agreed_price,provider_transaction_id=f'RECETTE-{ride.pk}',confirmed_at=now)
            FleetRemittance.objects.get_or_create(motorcycle=bike,period_start=today,period_end=today,defaults={'gross_revenue':12000,'commission_amount':1200,'net_amount':10800})
            SupportTicket.objects.get_or_create(requester=u,subject=f'RECETTE · Vérification de versement {i}',defaults={'message':'Dossier de recette pour vérifier le traitement DG. Aucun transfert réel.','priority':'high' if i==0 else 'medium'})
        Notification.objects.get_or_create(user=dg,title='RECETTE · Réseau prêt à vérifier',defaults={'kind':'system','body':'6 motards, flotte, courses, paiements et GPS persistés pour la recette.'})
        self.stdout.write(self.style.SUCCESS(f'Données de recette créées. DG : {dg.phone_number}. Comptes existants conservés.'))
