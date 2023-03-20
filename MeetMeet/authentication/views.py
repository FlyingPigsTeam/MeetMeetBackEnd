from . import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from . import models
from rest_framework_simplejwt.tokens import RefreshToken
from .utils import Util
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
import jwt
from django.conf import settings


@api_view(["POST"])
def Register(request):
    jsonData = request.data
    user_data = serializers.RegisterSerializer(data=jsonData)
    if user_data.is_valid():
        user_data.save()

        # verification
        user = models.User.objects.get(email=user_data.data['email'])
        token = RefreshToken.for_user(user).access_token
        current_site = str(get_current_site(request))
        relativeLink = reverse('email-verify')
        absURL = 'http://'+current_site+relativeLink+'?token='+str(token)
        email_body = 'Hi ' + user.username + \
            ' Use link below to verify your email \n '+absURL
        email_data = {'email_body': email_body,
                      'email_subject': 'Verify Your Email', 'to': user.email}

        Util.send_email(email_data)

        return Response({"status": "success"}, status=status.HTTP_201_CREATED)
    else:
        return Response({"status": "fail", "message": user_data.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
def verifyEmail(request):
    token = request.GET.get('token')
    try:
        payload = jwt.decode(token,settings.SECRET_KEY, algorithms=['HS256'])
        userID = payload['user_id']
        user = models.User.objects.get(id=userID)
        if not user.email_verified :
            user.email_verified=True
            user.save()
        return Response({'success' : 'user successfully verified'},status=status.HTTP_200_OK)
    except jwt.ExpiredSignatureError:
        return Response({'error': 'activation expired'}, status=status.HTTP_400_BAD_REQUEST)
    except jwt.exceptions.DecodeError:
        return Response({'error': 'token is invalid'}, status=status.HTTP_400_BAD_REQUEST)