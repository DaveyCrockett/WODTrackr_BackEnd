from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    register,
    user_profile,
    update_profile,
    update_profile_details,
    user_preferences,
    update_preferences,
    create_guest_session,
    stripe_config,
    create_stripe_checkout_session,
    create_stripe_billing_portal_session,
    stripe_webhook,
)

urlpatterns = [
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', register, name='register'),
    path('auth/guest/', create_guest_session, name='create_guest_session'),
    path('billing/stripe/config/', stripe_config, name='stripe_config'),
    path('billing/stripe/checkout-session/', create_stripe_checkout_session, name='create_stripe_checkout_session'),
    path('billing/stripe/portal-session/', create_stripe_billing_portal_session, name='create_stripe_billing_portal_session'),
    path('billing/stripe/webhook/', stripe_webhook, name='stripe_webhook'),
    path('profile/', user_profile, name='user_profile'),
    path('profile/update/', update_profile, name='update_profile'),
    path('profile/update/details/', update_profile_details, name='update_profile_details'),
    path('preferences/', user_preferences, name='user_preferences'),
    path('preferences/update/', update_preferences, name='update_preferences'),
]
