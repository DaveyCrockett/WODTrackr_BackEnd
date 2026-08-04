import logging

import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
import uuid
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from .serializers import RegisterSerializer, UserSerializer, UserProfileSerializer, UserPreferenceSerializer, CustomTokenObtainPairSerializer, GuestSessionSerializer
from .models import GuestSession, LoginAttempt, UserProfile, UserPreference, RememberMeToken


logger = logging.getLogger(__name__)


STRIPE_PRICE_SETTING_MAP = {
    'monthly_free': 'STRIPE_DEFAULT_PRICE_MONTHLY_FREE_ID',
    'monthly_individual_plus': 'STRIPE_DEFAULT_PRICE_MONTHLY_INDIVIDUAL_PLUS_ID',
    'monthly_individual_pro': 'STRIPE_DEFAULT_PRICE_MONTHLY_INDIVIDUAL_PRO_ID',
    'annual_individual_plus': 'STRIPE_DEFAULT_PRICE_ANNUAL_INDIVIDUAL_PLUS_ID',
    'annual_individual_pro': 'STRIPE_DEFAULT_PRICE_ANNUAL_INDIVIDUAL_PRO_ID',
    'starter_gym': 'STRIPE_DEFAULT_PRICE_STARTER_GYM_ID',
    'growth_gym': 'STRIPE_DEFAULT_PRICE_GROWTH_GYM_ID',
    'pro_gym': 'STRIPE_DEFAULT_PRICE_PRO_GYM_ID',
}


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
        remember_me_raw = request.data.get('remember_me', False)
        remember_me = False

        if isinstance(remember_me_raw, bool):
            remember_me = remember_me_raw
        elif isinstance(remember_me_raw, str):
            remember_me = remember_me_raw.strip().lower() in ('1', 'true', 'yes', 'on')
        elif isinstance(remember_me_raw, int):
            remember_me = remember_me_raw == 1
        
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
                if remember_me:
                    try:
                        remember_token = RememberMeToken.objects.create(
                            user=user,
                            token=str(uuid.uuid4()),
                            ip_address=ip_address if ip_address != '0.0.0.0' else None,
                            user_agent=user_agent,
                            expires_at=timezone.now() + timedelta(days=30)
                        )
                        response.data['remember_me_token'] = remember_token.token
                        response.data['remember_me_expires_at'] = remember_token.expires_at.isoformat()
                    except Exception:
                        # Do not block login if remember-me token creation fails.
                        response.data['remember_me_token'] = None
                        response.data['remember_me_expires_at'] = None
            except User.DoesNotExist:
                pass
            
            return response
            
        except (InvalidToken, TokenError, AuthenticationFailed) as e:
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


def _is_stripe_configured():
    return bool(settings.STRIPE_PUBLISHABLE_KEY and settings.STRIPE_SECRET_KEY)


def _stripe_price_catalog():
    catalog = {}
    for plan_key, setting_name in STRIPE_PRICE_SETTING_MAP.items():
        value = getattr(settings, setting_name, '')
        if value:
            catalog[plan_key] = value
    return catalog


def _stripe_frontend_settings_payload():
    return {
        'publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
        'default_price_id': settings.STRIPE_DEFAULT_PRICE_ID,
        'price_catalog': _stripe_price_catalog(),
        'configured': _is_stripe_configured(),
        'urls': {
            'success_url': settings.STRIPE_SUCCESS_URL,
            'cancel_url': settings.STRIPE_CANCEL_URL,
            'billing_portal_return_url': getattr(
                settings,
                'STRIPE_BILLING_PORTAL_RETURN_URL',
                settings.STRIPE_SUCCESS_URL,
            ),
        },
    }


def _resolve_checkout_price(request_data):
    # Direct price_id takes precedence to support custom catalog entries from frontend.
    explicit_price_id = request_data.get('price_id') if isinstance(request_data, dict) else None
    if explicit_price_id:
        return explicit_price_id, None

    plan_key = request_data.get('plan_key') if isinstance(request_data, dict) else None
    if plan_key:
        catalog = _stripe_price_catalog()
        return catalog.get(plan_key, ''), plan_key

    return settings.STRIPE_DEFAULT_PRICE_ID, None


def _get_or_create_stripe_customer(user):
    if not user.email:
        customer = stripe.Customer.create(
            name=user.username,
            metadata={
                'user_id': str(user.id),
                'username': user.username,
            },
        )
        return customer.id

    existing_customers = stripe.Customer.list(email=user.email, limit=1)
    existing = existing_customers.data[0] if existing_customers.data else None
    if existing:
        return existing.id

    customer = stripe.Customer.create(
        email=user.email,
        name=user.username,
        metadata={
            'user_id': str(user.id),
            'username': user.username,
        },
    )
    return customer.id


@api_view(['GET'])
@permission_classes([AllowAny])
def stripe_config(request):
    """
    Return frontend-safe Stripe configuration.
    """
    return Response(
        {
            'data': _stripe_frontend_settings_payload()
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def stripe_settings(request):
    """
    Return Stripe settings used by the frontend, including configured redirect URLs.
    """
    return Response(
        {
            'data': _stripe_frontend_settings_payload()
        },
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_stripe_checkout_session(request):
    """
    Create a Stripe Checkout Session for subscription or one-time payment.
    """
    if not _is_stripe_configured():
        return Response(
            {
                'error': 'Stripe is not configured',
                'detail': 'Set STRIPE_PUBLISHABLE_KEY and STRIPE_SECRET_KEY in your environment.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    mode = request.data.get('mode', 'subscription')
    if mode not in ('subscription', 'payment'):
        return Response(
            {
                'error': 'Invalid checkout mode',
                'detail': "mode must be either 'subscription' or 'payment'."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    price_id, plan_key = _resolve_checkout_price(request.data)
    if not price_id:
        return Response(
            {
                'error': 'Missing price id',
                'detail': 'Provide price_id, a valid plan_key, or set STRIPE_DEFAULT_PRICE_ID.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        quantity = int(request.data.get('quantity', 1))
    except (TypeError, ValueError):
        return Response(
            {
                'error': 'Invalid quantity',
                'detail': 'quantity must be a positive integer.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    if quantity < 1:
        return Response(
            {
                'error': 'Invalid quantity',
                'detail': 'quantity must be at least 1.'
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        checkout_kwargs = {
            'mode': mode,
            'line_items': [
                {
                    'price': price_id,
                    'quantity': quantity,
                }
            ],
            'success_url': settings.STRIPE_SUCCESS_URL,
            'cancel_url': settings.STRIPE_CANCEL_URL,
            'metadata': {
                'user_id': str(request.user.id),
                'username': request.user.username,
            },
        }

        if plan_key:
            checkout_kwargs['metadata']['plan_key'] = plan_key

        if request.user.email:
            checkout_kwargs['customer_email'] = request.user.email

        if mode == 'subscription':
            checkout_kwargs['allow_promotion_codes'] = True

        checkout_session = stripe.checkout.Session.create(**checkout_kwargs)
    except stripe.StripeError as exc:
        return Response(
            {
                'error': 'Stripe request failed',
                'detail': str(exc)
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response(
        {
            'message': 'Checkout session created',
            'data': {
                'id': checkout_session.id,
                'url': checkout_session.url,
                'mode': mode,
                'price_id': price_id,
                'plan_key': plan_key,
            },
        },
        status=status.HTTP_201_CREATED
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_stripe_billing_portal_session(request):
    """
    Create a Stripe Billing Portal session for subscription management.
    """
    if not _is_stripe_configured():
        return Response(
            {
                'error': 'Stripe is not configured',
                'detail': 'Set STRIPE_PUBLISHABLE_KEY and STRIPE_SECRET_KEY in your environment.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY
    return_url = request.data.get('return_url') or getattr(
        settings,
        'STRIPE_BILLING_PORTAL_RETURN_URL',
        settings.STRIPE_SUCCESS_URL,
    )

    try:
        customer_id = _get_or_create_stripe_customer(request.user)
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
    except stripe.StripeError as exc:
        return Response(
            {
                'error': 'Stripe billing portal request failed',
                'detail': str(exc),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(
        {
            'message': 'Billing portal session created',
            'data': {
                'url': portal_session.url,
            }
        },
        status=status.HTTP_201_CREATED,
    )


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """
    Handle Stripe webhooks with signature verification.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        return Response(
            {
                'error': 'Stripe webhook is not configured',
                'detail': 'Set STRIPE_WEBHOOK_SECRET in your environment.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY

    payload = request.body
    signature = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError:
        return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
    except stripe.SignatureVerificationError:
        return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

    event_type = event.get('type')
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        logger.info('Stripe checkout completed for session %s', session.get('id'))
    elif event_type == 'customer.subscription.updated':
        subscription = event['data']['object']
        logger.info(
            'Stripe subscription updated: %s status=%s',
            subscription.get('id'),
            subscription.get('status'),
        )
    elif event_type == 'customer.subscription.deleted':
        subscription = event['data']['object']
        logger.info('Stripe subscription deleted: %s', subscription.get('id'))
    elif event_type == 'payment_intent.payment_failed':
        intent = event['data']['object']
        logger.warning('Stripe payment failed for payment intent %s', intent.get('id'))

    return Response({'received': True}, status=status.HTTP_200_OK)


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
            # Create UserPreference for the new user
            UserPreference.objects.get_or_create(user=user)
            
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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_preferences(request):
    """
    Get current user preferences.
    """
    try:
        preferences, _ = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(preferences)
        return Response(
            {
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {
                'error': 'Failed to retrieve preferences',
                'detail': 'An error occurred while retrieving your preferences. Please try again.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_preferences(request):
    """
    Update current user preferences.
    """
    try:
        preferences, _ = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(preferences, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Preferences updated successfully',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                'error': 'Invalid preferences data',
                'detail': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {
                'error': 'Failed to update preferences',
                'detail': 'An error occurred while updating your preferences. Please try again.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

