from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User
from apps.rides.models import Ride
from apps.payments.models import Payment
from .models import SimulationRun, LocationPing
from .simulation import frame_at, advance, interpolate, distance, trip_progress

class SimulationTests(TestCase):
    def setUp(self):
        geometry=[[15.30,-4.30],[15.31,-4.30],[15.32,-4.30]]
        lengths=[0,distance(geometry[0],geometry[1]),distance(geometry[0],geometry[1])*2]
        self.road={'coordinates':geometry,'lengths':lengths,'distance':lengths[-1]}
        self.routes=[{'id':1,'moto':'Moto SIM','client':'Client SIM','label':'Recette','approach':self.road,'trip':self.road,'source':'test'}]
    def test_distance_progress_stops_jam_and_arrival(self):
        d=self.road['distance'];cruise=d*.35/(30/3.6)
        a=trip_progress(cruise+10,d);self.assertEqual(a[2],'embouteillage');self.assertEqual(a[1],5)
        stop=cruise+d*.15/(5/3.6)+d*.15/(30/3.6)
        self.assertEqual(trip_progress(stop+1,d)[2],'arret')
        self.assertEqual(trip_progress(stop+1,d)[0],trip_progress(stop+12,d)[0])
        self.assertTrue(trip_progress(100000,d)[3])
        self.assertEqual(interpolate(self.road,d),self.road['coordinates'][-1])
    def test_client_waits_then_shares_motorcycle_and_state_is_durable(self):
        start=frame_at(self.routes,10)
        self.assertEqual(start['clients'][0]['phase'],'attente_moto')
        self.assertEqual(start['clients'][0]['longitude'],15.30)
        pickup=self.road['distance']/(24/3.6)
        onboard=frame_at(self.routes,pickup+100)
        self.assertEqual(onboard['vehicles'][0]['longitude'],onboard['clients'][0]['longitude'])
        run=SimulationRun.objects.create(name='Test',status='running',routes=self.routes)
        advance(run.pk,10);run.refresh_from_db();self.assertEqual(run.elapsed,10)
        run.status='paused';run.save();advance(run.pk,10);run.refresh_from_db();self.assertEqual(run.elapsed,10)
        self.assertEqual(Ride.objects.count(),0);self.assertEqual(Payment.objects.count(),0);self.assertEqual(LocationPing.objects.count(),0)
    def test_controls_are_operator_only_and_get_does_not_advance_time(self):
        run=SimulationRun.objects.create(name='Test',routes=self.routes,frame=frame_at(self.routes,0))
        client=User.objects.create_user('+2430001','long-password',role='client')
        dg=User.objects.create_user('+2430002','long-password',role='operator')
        api=APIClient();api.force_authenticate(client)
        self.assertEqual(api.post('/api/personnel/direction/',{'action':'simulation_step','id':run.pk},format='json').status_code,403)
        api.force_authenticate(dg)
        for _ in range(2):self.assertEqual(api.get('/api/personnel/direction/').status_code,200)
        run.refresh_from_db();self.assertEqual(run.elapsed,0)
        self.assertEqual(api.post('/api/personnel/direction/',{'action':'simulation_step','id':run.pk},format='json').status_code,200)
        run.refresh_from_db();self.assertEqual(run.elapsed,10);self.assertEqual(run.status,'paused')

    def test_transient_sqlite_lock_retries_the_rolled_back_tick(self):
        from unittest.mock import patch
        from django.db import OperationalError
        with patch('apps.geoloc.simulation._advance',side_effect=[OperationalError('database is locked'),'ok']) as tick, patch('apps.geoloc.simulation.time.sleep'):
            self.assertEqual(advance(1,10),'ok')
            self.assertEqual(tick.call_count,2)

    def test_recorded_motorcycle_trajectory_is_chronological(self):
        from .services import latest_positions_for
        user=User.objects.create_user('+2430042','long-password',role='motard')
        dg=User.objects.create_user('+2430043','long-password',role='operator')
        for lon in ['15.300000','15.301000','15.302000']:
            LocationPing.objects.create(user=user,latitude='-4.300000',longitude=lon)
        row=latest_positions_for(dg)[0]
        self.assertEqual(row['trajectory'],[[15.3,-4.3],[15.301,-4.3],[15.302,-4.3]])
        self.assertEqual(row['longitude'],15.302)
