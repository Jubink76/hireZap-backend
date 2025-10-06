# accounts/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
import logging

logger = logging.getLogger(__name__)

class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads the token from cookies instead of headers
    """
    def authenticate(self, request):
        # Try to get token from cookie
        raw_token = request.COOKIES.get('access')
        
        if raw_token is None:
            logger.debug("No access token found in cookies")
            return None
        
        logger.debug(f"Found access token in cookie: {raw_token[:20]}...")
        
        # Validate the token
        validated_token = self.get_validated_token(raw_token)
        
        # Get the user
        user = self.get_user(validated_token)
        
        logger.debug(f"Authenticated user: {user}")
        
        return (user, validated_token)