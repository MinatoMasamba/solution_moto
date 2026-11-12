from django.conf import settings
from django.db import models


class PersonnelProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='personnel_profile')
    photo = models.ImageField(upload_to='personnel/avatars/', blank=True)
    theme = models.CharField(max_length=10, choices=[('light','Clair'),('dark','Sombre'),('system','Système')], default='light')
    updated_at = models.DateTimeField(auto_now=True)
