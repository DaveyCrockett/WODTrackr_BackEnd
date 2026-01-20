from rest_framework.permissions import BasePermission, IsAuthenticated


class IsAuthenticatedOrGuest(BasePermission):
    """
    Permission that allows both authenticated users and guest session holders.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if request.user and request.user.is_authenticated:
            return True
        
        # Check if guest session exists
        if hasattr(request, 'guest_session') and request.guest_session:
            return True
        
        return False


class IsGuest(BasePermission):
    """
    Permission that only allows guest session holders.
    """
    
    def has_permission(self, request, view):
        return hasattr(request, 'guest_session') and request.guest_session is not None


class IsAuthenticatedUser(IsAuthenticated):
    """
    Permission that only allows authenticated registered users (not guests).
    """
    
    def has_permission(self, request, view):
        # Ensure user is authenticated AND not using guest session
        return (request.user and 
                request.user.is_authenticated and 
                not hasattr(request, 'guest_session'))
