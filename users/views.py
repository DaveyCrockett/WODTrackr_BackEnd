from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from .serializers import RegisterSerializer, UserSerializer, UserProfileSerializer, CustomTokenObtainPairSerializer, GuestSessionSerializer
from .models import GuestSession, LoginAttempt, UserProfile


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token view that logs login attempts for security monitoring.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        # Get client metadata
        ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        username = request.data.get('username', '')
        
        try:
            # Attempt authentication
            response = super().post(request, *args, **kwargs)
            
            # Log successful login
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            
            # Update user profile last_login
            try:
                user = User.objects.get(username=username)
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.last_login = timezone.now()
                profile.save()
            except User.DoesNotExist:
                pass
            
            return response
            
        except (InvalidToken, TokenError) as e:
            # Log failed login
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False
            )
            
            return Response(
                {
                    'error': 'Invalid credentials',
                    'detail': 'The username or password is incorrect.'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            # Log failed login for any other error
            LoginAttempt.objects.create(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                success=False
            )
            
            return Response(
                {
                    'error': 'Authentication failed',
                    'detail': 'An error occurred during authentication. Please try again.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


@api_view(['POST'])
@permission_classes([AllowAny])
def create_guest_session(request):
    """
    Create a guest session token for unauthenticated users.
    Guests can access limited functionality without registering.
    
    Optional parameters:
    - duration_hours (int): Session duration in hours (default: 24)
    """
    try:
        # Get client IP and user agent
        ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Optional: duration in hours from request (default 24)
        duration_hours = 24
        if isinstance(request.data, dict) and 'duration_hours' in request.data:
            try:
                duration_hours = int(request.data.get('duration_hours', 24))
                if duration_hours < 1 or duration_hours > 168:  # Max 7 days
                    return Response(
                        {
                            'error': 'Invalid duration',
                            'detail': 'Duration must be between 1 and 168 hours (7 days).'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except (ValueError, TypeError):
                return Response(
                    {
                        'error': 'Invalid duration format',
                        'detail': 'Duration must be a valid integer.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create guest session
        guest_session = GuestSession.create_session(
            ip_address=ip_address,
            user_agent=user_agent,
            duration_hours=duration_hours
        )
        
        serializer = GuestSessionSerializer(guest_session)
        return Response(
            {
                'message': 'Guest session created successfully',
                'data': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        return Response(
            {
                'error': 'Failed to create guest session',
                'detail': 'An error occurred while creating the guest session. Please try again.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user with email and password.
    Creates a UserProfile automatically upon registration.
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            # Create UserProfile for the new user
            UserProfile.objects.get_or_create(user=user)
            
            return Response(
                {
                    'message': 'User created successfully',
                    'data': {
                        'username': user.username,
                        'email': user.email,
                        'id': user.id
                    }
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {
                    'error': 'Registration failed',
                    'detail': 'An error occurred during registration. Please try again.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    return Response(
        {
            'error': 'Invalid registration data',
            'detail': serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user profile with extended information.
    """
    try:
        serializer = UserSerializer(request.user)
        return Response(
            {
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {
                'error': 'Failed to retrieve profile',
                'detail': 'An error occurred while retrieving your profile. Please try again.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update current user profile information.
    """
    try:
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Profile updated successfully',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                'error': 'Invalid profile data',
                'detail': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {
                'error': 'Failed to update profile',
                'detail': 'An error occurred while updating your profile. Please try again.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile_details(request):
    """
    Update current user profile details (bio, phone number, profile picture).
    """
    try:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Profile details updated successfully',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                'error': 'Invalid profile details data',
                'detail': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {
                'error': 'Failed to update profile details',
                'detail': 'An error occurred while updating your profile details. Please try again.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

