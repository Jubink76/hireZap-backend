# your_app/auth_utils.py
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.http import JsonResponse

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }

def set_jwt_cookies(response, tokens):
    # Set access token as HttpOnly cookie
    # You can also set refresh token as cookie if you want refresh via cookie
    # Access cookie setup:
    response.set_cookie(
        key='access_token',
        value=tokens['access'],
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        max_age=30*60  # 30 minutes
    )
    # optionally send refresh as cookie:
    response.set_cookie(
        key='refresh_token',
        value=tokens['refresh'],
        httponly=True,
        secure=not settings.DEBUG,
        samesite='Lax',
        max_age=7*24*60*60
    )
    return response
