from django.conf import settings
from datetime import timedelta

COOKIE_SECURE = not getattr(settings, 'DEBUG', True)
SAMESITE = "None" if not getattr(settings, 'DEBUG', True) else "Lax"

def set_jwt_cookies(response, access_token: str, refresh_token: str, remember_me: bool = False):
    # access token - short lived
    response.set_cookie(
        key = "access",
        value = str(access_token),
        httponly = True,
        secure = COOKIE_SECURE,
        samesite = SAMESITE,
        max_age = 15 * 60,  # 15 minutes
        path = '/',
    )

    # refresh_token - longer lived
    refresh_max_age = 30 * 24 * 60 * 60 if remember_me else 7 * 24 * 60 * 60
    response.set_cookie(
        key = "refresh",
        value = str(refresh_token),
        httponly = True,
        secure = COOKIE_SECURE, # for dev only
        samesite = SAMESITE,
        max_age = refresh_max_age,
        path = '/',
    )

def clear_jwt_cookies(response):
    response.delete_cookie('access',path='/')
    response.delete_cookie('refresh', path='/')
    response.delete_cookie('refresh', path='/api/auth/')
    return response