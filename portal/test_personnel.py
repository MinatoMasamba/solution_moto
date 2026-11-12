from django.test import TestCase
from rest_framework.test import APIClient
from apps.users.models import User, Notification, SupportTicket, MotardProfile

class PersonnelTests(TestCase):
    def setUp(self):
        self.dg=User.objects.create_user('+243000001','secret-long-test',role='operator')
        self.client_user=User.objects.create_user('+243000002','secret-long-test',role='client')
        self.api=APIClient()
    def test_access_and_snapshot_scope(self):
        self.assertIn(self.api.get('/api/personnel/direction/').status_code,[401,403])
        self.api.force_authenticate(self.client_user)
        self.assertEqual(self.api.get('/api/personnel/direction/').status_code,403)
        Notification.objects.create(user=self.client_user,title='Private')
        n=Notification.objects.create(user=self.dg,title='DG')
        self.api.force_authenticate(self.dg)
        res=self.api.get('/api/personnel/direction/')
        self.assertEqual(res.status_code,200)
        self.assertEqual([x['id'] for x in res.data['notifications']],[n.pk])
        self.assertEqual(res.data['kpis']['total_rides'],0)
    def test_persisted_actions_and_cross_account_protection(self):
        self.api.force_authenticate(self.dg)
        n=Notification.objects.create(user=self.client_user,title='private')
        self.assertEqual(self.api.post('/api/personnel/direction/',{'action':'notification_read','id':n.pk},format='json').status_code,404)
        t=SupportTicket.objects.create(requester=self.client_user,subject='Support')
        self.assertEqual(self.api.post('/api/personnel/direction/',{'action':'support_status','id':t.pk,'status':'resolved'},format='json').status_code,200)
        t.refresh_from_db();self.assertIsNotNone(t.resolved_at)
        p=MotardProfile.objects.create(user=self.client_user)
        self.assertEqual(self.api.post('/api/personnel/direction/',{'action':'application','id':p.pk,'status':'approved'},format='json').status_code,200)
        p.refresh_from_db();self.assertEqual(p.application_status,'approved')
        self.assertEqual(self.api.post('/api/personnel/direction/',{'action':'support_status','id':t.pk,'status':'invented'},format='json').status_code,400)
