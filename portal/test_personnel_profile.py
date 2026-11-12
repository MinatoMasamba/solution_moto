import base64
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PIL import Image
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from apps.users.models import User
from .models import PersonnelProfile

class PersonnelProfileTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('+243000900091','long-password',role='operator',first_name='Marie')
        self.api=APIClient();self.api.force_authenticate(self.user)
    def test_profile_is_persisted_without_role_escalation(self):
        response=self.api.patch('/api/personnel/profile/',{'first_name':'Aline','last_name':'Kalonji','post_nom':'Mbuyi','email':'aline@example.invalid','phone_number':'+243000900092','theme':'dark','role':'owner','is_staff':True},format='json')
        self.assertEqual(response.status_code,200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role,'operator');self.assertFalse(self.user.is_staff)
        self.assertEqual(self.user.get_full_name(),'Aline Kalonji Mbuyi')
        self.assertEqual(PersonnelProfile.objects.get(user=self.user).theme,'dark')
        self.assertEqual(self.api.get('/api/personnel/profile/').data['phone_number'],'+243000900092')
    def test_invalid_profile_does_not_overwrite_data(self):
        User.objects.create_user('+243000900093','long-password')
        for body in [{'email':'invalid'},{'phone_number':'+243000900093'},{'photo_base64':'not-an-image'},{'theme':'unknown'},{'phone_number':'++243000900095'}]:
            self.assertEqual(self.api.patch('/api/personnel/profile/',body,format='json').status_code,400)
        self.user.refresh_from_db();self.assertEqual(self.user.first_name,'Marie')
    def test_avatar_upload_and_access_control(self):
        image=BytesIO();Image.new('RGB',(8,8),'blue').save(image,format='PNG')
        with TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            r=self.api.patch('/api/personnel/profile/',{'photo_base64':base64.b64encode(image.getvalue()).decode()},format='json')
            self.assertEqual(r.status_code,200);self.assertIn('/personnel/avatars/',r.data['photo_url'])
            p=PersonnelProfile.objects.get(user=self.user);self.assertTrue(p.photo.storage.exists(p.photo.name))
        client=User.objects.create_user('+243000900094','long-password',role='client')
        self.api.force_authenticate(client)
        self.assertEqual(self.api.get('/api/personnel/profile/').status_code,403)
    def test_map_poll_does_not_aggregate_other_tabs(self):
        with patch('portal.personnel_api.DashboardService.get_operator_kpis',side_effect=AssertionError('Global refresh forbidden')):
            response=self.api.get('/api/personnel/direction/map/')
        self.assertEqual(response.status_code,200)
        self.assertEqual(set(response.data),{'positions','simulation','updated_at'})
