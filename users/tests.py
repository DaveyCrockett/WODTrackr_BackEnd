from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import UserProfile, UserPreference, GuestSession
from users.serializers import UserSerializer, UserProfileSerializer, UserPreferenceSerializer
from django.utils import timezone
from datetime import timedelta


class UserProfileSerializerTest(TestCase):
    """Test cases for UserProfileSerializer"""
    
    def setUp(self):
        """Set up test user and profile"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            role='user',
            bio='Test bio',
            phone_number='1234567890',
            verified=False,
            two_factor_enabled=False
        )
    
    def test_profile_serializer_fields(self):
        """Test that UserProfileSerializer contains all required fields"""
        serializer = UserProfileSerializer(instance=self.user_profile)
        data = serializer.data
        
        # Check that all expected fields are present
        expected_fields = [
            'role', 'profile_picture', 'bio', 'phone_number',
            'verified', 'two_factor_enabled', 'created_at',
            'updated_at', 'last_login'
        ]
        for field in expected_fields:
            self.assertIn(field, data)
    
    def test_profile_serializer_read_only_fields(self):
        """Test that read-only fields cannot be updated"""
        data = {
            'verified': True,
            'two_factor_enabled': True,
            'role': 'admin'
        }
        serializer = UserProfileSerializer(instance=self.user_profile, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        
        # Refresh from database
        self.user_profile.refresh_from_db()
        
        # Read-only fields should not be updated
        self.assertFalse(self.user_profile.verified)
        self.assertFalse(self.user_profile.two_factor_enabled)
        self.assertEqual(self.user_profile.role, 'user')
    
    def test_profile_serializer_optional_fields(self):
        """Test that optional fields can be omitted"""
        data = {
            'bio': 'Updated bio'
        }
        serializer = UserProfileSerializer(instance=self.user_profile, data=data, partial=True)
        # Should be valid even without profile_picture and phone_number
        self.assertTrue(serializer.is_valid())


class UserSerializerTest(TestCase):
    """Test cases for UserSerializer with nested profile"""
    
    def setUp(self):
        """Set up test user and profile"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            role='user',
            bio='Test bio',
            phone_number='1234567890'
        )
        self.user_preferences = UserPreference.objects.create(
            user=self.user,
            preferred_units='kg',
            time_format='24h',
            notifications_email=True,
            notifications_push=False,
            theme='dark',
            timezone='UTC',
            locale='en-US',
            public_profile=True,
            default_rest_timer_seconds=120,
            metric_rounding=5
        )
    
    def test_user_serializer_includes_profile(self):
        """Test that UserSerializer includes nested profile data"""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        
        # Check that profile field is present
        self.assertIn('profile', data)
        
        # Check that profile contains expected fields
        profile = data['profile']
        self.assertEqual(profile['role'], 'user')
        self.assertEqual(profile['bio'], 'Test bio')
        self.assertEqual(profile['phone_number'], '1234567890')

    def test_user_serializer_includes_preferences(self):
        """Test that UserSerializer includes nested preferences data"""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data

        self.assertIn('preferences', data)
        preferences = data['preferences']
        self.assertEqual(preferences['preferred_units'], 'kg')
        self.assertEqual(preferences['time_format'], '24h')
        self.assertEqual(preferences['notifications_push'], False)
        self.assertEqual(preferences['theme'], 'dark')
    
    def test_user_serializer_without_profile(self):
        """Test that UserSerializer handles users without profiles gracefully"""
        user_no_profile = User.objects.create_user(
            username='noprofile',
            email='noprofile@example.com'
        )
        
        serializer = UserSerializer(instance=user_no_profile)
        data = serializer.data
        
        # Profile field should be present but None
        self.assertIn('profile', data)
        self.assertIsNone(data['profile'])

        # Preferences field should be present but None
        self.assertIn('preferences', data)
        self.assertIsNone(data['preferences'])
    
    def test_user_serializer_all_fields(self):
        """Test that UserSerializer contains all expected user fields"""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        
        expected_fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile', 'preferences']
        for field in expected_fields:
            self.assertIn(field, data)
        
        # Verify user data
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['first_name'], 'Test')
        self.assertEqual(data['last_name'], 'User')
    
    def test_user_serializer_profile_read_only(self):
        """Test that profile field is read-only in UserSerializer"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'profile': {
                'role': 'admin',
                'bio': 'Updated bio'
            }
        }
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        
        # Serializer should be valid
        self.assertTrue(serializer.is_valid())
        serializer.save()
        
        # Refresh from database
        self.user.profile.refresh_from_db()
        
        # Profile should not be updated (it's read-only)
        self.assertEqual(self.user.profile.role, 'user')
        self.assertEqual(self.user.profile.bio, 'Test bio')


class UserPreferenceSerializerTest(TestCase):
    """Test cases for UserPreferenceSerializer"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='prefuser',
            email='pref@example.com'
        )
        self.preferences = UserPreference.objects.create(
            user=self.user,
            preferred_units='lbs',
            time_format='12h',
            notifications_email=True,
            notifications_push=True,
            theme='system',
            timezone='UTC',
            locale='en-US',
            public_profile=True,
            default_rest_timer_seconds=90,
            metric_rounding=5
        )

    def test_preferences_serializer_fields(self):
        serializer = UserPreferenceSerializer(instance=self.preferences)
        data = serializer.data

        expected_fields = [
            'preferred_units', 'time_format', 'notifications_email', 'notifications_push',
            'reminder_time', 'theme', 'timezone', 'locale', 'public_profile',
            'default_rest_timer_seconds', 'metric_rounding', 'created_at', 'updated_at'
        ]
        for field in expected_fields:
            self.assertIn(field, data)

    def test_preferences_serializer_read_only_fields(self):
        data = {
            'created_at': timezone.now(),
            'updated_at': timezone.now()
        }
        serializer = UserPreferenceSerializer(instance=self.preferences, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()

        self.preferences.refresh_from_db()
        self.assertIsNotNone(self.preferences.created_at)
        self.assertIsNotNone(self.preferences.updated_at)

    def test_preferences_serializer_invalid_choice(self):
        data = {
            'preferred_units': 'stones'
        }
        serializer = UserPreferenceSerializer(instance=self.preferences, data=data, partial=True)
        self.assertFalse(serializer.is_valid())


class UserPreferencesAPITest(TestCase):
    """Integration tests for user preferences API"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='apiuser',
            email='api@example.com',
            password='password123'
        )
        self.preferences = UserPreference.objects.create(user=self.user)

    def authenticate(self):
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    def test_get_preferences_requires_auth(self):
        response = self.client.get('/api/users/preferences/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_preferences_success(self):
        self.authenticate()
        response = self.client.get('/api/users/preferences/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)

    def test_update_preferences_success(self):
        self.authenticate()
        payload = {
            'preferred_units': 'kg',
            'time_format': '24h',
            'notifications_push': False,
            'theme': 'dark',
            'default_rest_timer_seconds': 120
        }
        response = self.client.put('/api/users/preferences/update/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['preferred_units'], 'kg')
        self.assertEqual(response.data['data']['time_format'], '24h')
        self.assertEqual(response.data['data']['notifications_push'], False)
        self.assertEqual(response.data['data']['theme'], 'dark')

    def test_update_preferences_invalid_choice(self):
        self.authenticate()
        payload = {
            'preferred_units': 'stones'
        }
        response = self.client.put('/api/users/preferences/update/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthFlowAPITest(TestCase):
    """End-to-end tests for common authentication flows and edge cases."""

    def setUp(self):
        self.client = APIClient()
        self.user_password = 'StrongPass123!'
        self.user = User.objects.create_user(
            username='authuser',
            email='authuser@example.com',
            password=self.user_password
        )

    def _login(self, payload=None):
        if payload is None:
            payload = {
                'username': self.user.username,
                'password': self.user_password
            }
        return self.client.post('/api/users/auth/login/', payload, format='json')

    def test_register_success(self):
        payload = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        response = self.client.post('/api/users/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['username'], 'newuser')

    def test_register_password_mismatch(self):
        payload = {
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': 'ComplexPass123!',
            'password2': 'DifferentPass123!'
        }
        response = self.client.post('/api/users/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data['detail'])

    def test_register_duplicate_username(self):
        payload = {
            'username': self.user.username,
            'email': 'another@example.com',
            'password': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        }
        response = self.client.post('/api/users/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['detail'])

    def test_login_success(self):
        response = self._login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_credentials(self):
        response = self._login({'username': self.user.username, 'password': 'WrongPass123!'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error'], 'Invalid credentials')

    def test_login_with_remember_me(self):
        response = self._login({'username': self.user.username, 'password': self.user_password, 'remember_me': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('remember_me_token', response.data)
        self.assertIn('remember_me_expires_at', response.data)
        self.assertIsNotNone(response.data['remember_me_token'])

    def test_refresh_token_success(self):
        login_response = self._login()
        refresh = login_response.data['refresh']
        response = self.client.post('/api/users/auth/refresh/', {'refresh': refresh}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_refresh_token_invalid(self):
        response = self.client.post('/api/users/auth/refresh/', {'refresh': 'badtoken'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_guest_session_created(self):
        response = self.client.post('/api/users/auth/guest/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access_token', response.data['data'])
        self.assertIn('expires_at', response.data['data'])

    def test_guest_session_invalid_duration(self):
        response = self.client.post('/api/users/auth/guest/', {'duration_hours': 500}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('duration', response.data['error'].lower())

    def test_profile_requires_auth(self):
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_success(self):
        login_response = self._login()
        access = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['username'], self.user.username)

    def test_profile_denied_for_guest_token(self):
        guest = GuestSession.create_session(duration_hours=24, user_agent='test-agent', ip_address='127.0.0.1')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {guest.token}')
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_profile_denied_for_invalid_guest_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer guest_invalid')
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_denied_for_expired_guest_token(self):
        expired = GuestSession.create_session(duration_hours=1, user_agent='test-agent', ip_address='127.0.0.1')
        expired.expires_at = timezone.now() - timedelta(hours=1)
        expired.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired.token}')
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

