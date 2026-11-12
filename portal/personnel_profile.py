import re
import base64
import binascii
from io import BytesIO
from uuid import uuid4
from PIL import Image, UnidentifiedImageError
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import PersonnelProfile
from .views import IsOperator
from apps.users.models import User


class ProfileUpdate(serializers.ModelSerializer):
    theme = serializers.ChoiceField(choices=['light','dark','system'], required=False)
    photo_base64 = serializers.CharField(required=False, trim_whitespace=False, max_length=1500000)

    class Meta:
        model = User
        fields = ['first_name','last_name','post_nom','email','phone_number','theme','photo_base64']

    def validate_phone_number(self, value):
        value=value.replace(' ','')
        if not re.fullmatch(r'\+?\d{8,15}',value):
            raise serializers.ValidationError('Numéro de téléphone invalide.')
        if User.objects.filter(phone_number=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError('Ce numéro est déjà utilisé.')
        return value

    def validate_photo_base64(self, value):
        try:
            raw=base64.b64decode(value,validate=True)
            if len(raw)>1024*1024: raise ValueError()
            with Image.open(BytesIO(raw)) as im:
                if im.format not in ('JPEG','PNG') or im.width*im.height>16000000: raise ValueError()
                im.load();im.thumbnail((1024,1024))
                output=BytesIO();im.convert('RGB').save(output,format='JPEG',quality=88)
                return output.getvalue()
        except (ValueError,binascii.Error,UnidentifiedImageError,OSError,Image.DecompressionBombError):
            raise serializers.ValidationError('Choisir une image PNG/JPEG de moins de 1 Mo (16 mégapixels maximum).')


def profile_data(user, request):
    p=PersonnelProfile.objects.filter(user=user).first()
    return {'id':user.pk,'first_name':user.first_name,'last_name':user.last_name,'post_nom':user.post_nom,
            'name':user.get_full_name() or user.phone_number,'phone_number':user.phone_number,'email':user.email,
            'role':user.get_role_display(),'is_verified':user.is_verified,'is_active':user.is_active,
            'date_joined':user.date_joined,'last_login':user.last_login,
            'theme':p.theme if p else 'light','photo_url':request.build_absolute_uri(p.photo.url) if p and p.photo else None}


class PersonnelProfileView(APIView):
    permission_classes=[IsOperator]

    def get(self,request):
        return Response(profile_data(request.user,request))

    @transaction.atomic
    def patch(self,request):
        serializer=ProfileUpdate(request.user,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        values=dict(serializer.validated_data)
        theme=values.pop('theme',None);photo=values.pop('photo_base64',None)
        for key,value in values.items():setattr(request.user,key,value)
        if values:request.user.save(update_fields=list(values))
        if theme is not None or photo is not None:
            p,_=PersonnelProfile.objects.get_or_create(user=request.user)
            if theme is not None:p.theme=theme
            if photo is not None:p.photo.save(f'{uuid4().hex}.jpg',ContentFile(photo),save=False)
            p.save()
        return Response(profile_data(request.user,request))
