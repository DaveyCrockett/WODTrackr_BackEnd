from rest_framework.authentication import TokenAuthentication, BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import GuestSession
from django.contrib.auth.models import AnonymousUser


class GuestSessionAuthentication(BaseAuthentication):
    """
    Custom authentication backend for guest session tokens.
    Allows unauthenticated users to access limited functionality using a guest token.
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '').split()
        
        if len(auth_header) != 2 or auth_header[0].lower() != 'bearer':
            return None
        
        token = auth_header[1]
        
        # Check if it's a guest token (starts with 'guest_')
        if not token.startswith('guest_'):
            return None
        
        try:
            # Fetch the guest session
            guest_session = GuestSession.objects.get(token=token)
            
            # Check if session is valid
            if not guest_session.is_valid():
                raise AuthenticationFailed('Guest session has expired or is inactive')
            
            # Return a tuple of (user, auth) where user is AnonymousUser for guests
            # We attach the guest session to request for later use
            request.guest_session = guest_session
            return (AnonymousUser(), None)
        
        except GuestSession.DoesNotExist:
            raise AuthenticationFailed('Invalid guest token')
    
    def authenticate_header(self, request):
        return 'Bearer'


class GuestTokenAuthentication(TokenAuthentication):
    """
    Extended TokenAuthentication that supports both regular auth tokens and guest tokens.
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '').split()
        
        if len(auth_header) != 2 or auth_header[0].lower() != 'bearer':
            return None
        
        token = auth_header[1]
        
        # Try guest session authentication first
        if token.startswith('guest_'):
            try:
                guest_session = GuestSession.objects.get(token=token)
                if not guest_session.is_valid():
                    raise AuthenticationFailed('Guest session has expired or is inactive')
                request.guest_session = guest_session
                return (AnonymousUser(), None)
            except GuestSession.DoesNotExist:
                raise AuthenticationFailed('Invalid guest token')
        
        # Fall back to regular token authentication
        return super().authenticate(request)
