# utils.py or wherever you have these functions
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
import logging

logger = logging.getLogger(__name__)

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }

def set_jwt_cookies(response, access_token: str, refresh_token: str, remember_me: bool = False):
    # Access token
    response.set_cookie(
        key='access',
        value=str(access_token),
        max_age=3600,
        httponly=True,
        secure=False,
        samesite='Lax',  # Lax works now because of proxy
        path='/',
    )
    
    # Refresh token
    refresh_max_age = (30 * 24 * 60 * 60) if remember_me else (7 * 24 * 60 * 60)
    response.set_cookie(
        key='refresh',
        value=str(refresh_token),
        max_age=refresh_max_age,
        httponly=True,
        secure=False,
        samesite='Lax',
        path='/',
    )
    
    return response

def clear_jwt_cookies(response):
    """Clear JWT cookies on logout"""
    response.delete_cookie('access', path='/', samesite='Lax')
    response.delete_cookie('refresh', path='/', samesite='Lax')
    logger.debug("Cleared JWT cookies")
    return response


def debug_request_cookies(request):
    """Helper function to debug cookies in any view"""
    logger.info("=" * 80)
    logger.info("REQUEST COOKIE DEBUG")
    logger.info(f"All cookies: {dict(request.COOKIES)}")
    logger.info(f"Has access: {'access' in request.COOKIES}")
    logger.info(f"Has refresh: {'refresh' in request.COOKIES}")
    if 'access' in request.COOKIES:
        logger.info(f"Access (first 30): {request.COOKIES['access'][:30]}...")
    logger.info("=" * 80)