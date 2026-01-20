from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from users.models import UserProfile, GuestSession, LoginAttempt
from django.utils import timezone


class AuthenticationTestCase(APITestCase):
    """Integration tests for authentication endpoints"""
    
    def setUp(self):
        """Set up test client and test data"""
        self.client = APIClient()
        self.register_url = '/api/users/auth/register/'
        self.login_url = '/api/users/auth/login/'
        self.refresh_url = '/api/users/auth/refresh/'
        self.guest_url = '/api/users/auth/guest/'
        
        # Test user data
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_user_registration_success(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['username'], 'testuser')
        
        # Verify user was created in database
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        
        # Verify UserProfile was created
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
    
    def test_user_registration_password_mismatch(self):
        """Test registration fails with mismatched passwords"""
        data = self.user_data.copy()
        data['password2'] = 'DifferentPass123!'
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_user_registration_duplicate_username(self):
        """Test registration fails with duplicate username"""
        # Create first user
        self.client.post(self.register_url, self.user_data, format='json')
        
        # Try to create duplicate
        response = self.client.post(self.register_url, self.user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_user_login_success(self):
        """Test successful user login"""
        # Register user first
        self.client.post(self.register_url, self.user_data, format='json')
        
        # Login
        login_data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Verify LoginAttempt was logged
        login_attempt = LoginAttempt.objects.filter(username='testuser').first()
        self.assertIsNotNone(login_attempt)
        self.assertTrue(login_attempt.success)
    
    def test_user_login_invalid_credentials(self):
        """Test login fails with invalid credentials"""
        # Register user first
        self.client.post(self.register_url, self.user_data, format='json')
        
        # Try to login with wrong password
        login_data = {
            'username': 'testuser',
            'password': 'WrongPassword123!'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        
        # Verify failed LoginAttempt was logged
        login_attempt = LoginAttempt.objects.filter(username='testuser').last()
        self.assertIsNotNone(login_attempt)
        self.assertFalse(login_attempt.success)
    
    def test_token_refresh(self):
        """Test JWT token refresh"""
        # Register and login
        self.client.post(self.register_url, self.user_data, format='json')
        login_data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Refresh token
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(self.refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_guest_session_creation(self):
        """Test guest session creation"""
        response = self.client.post(self.guest_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertIn('access_token', response.data['data'])
        self.assertTrue(response.data['data']['access_token'].startswith('guest_'))
        
        # Verify guest session in database
        guest_token = response.data['data']['access_token']
        guest_session = GuestSession.objects.get(token=guest_token)
        self.assertTrue(guest_session.is_valid())
    
    def test_guest_session_with_custom_duration(self):
        """Test guest session with custom duration"""
        response = self.client.post(
            self.guest_url,
            {'duration_hours': 48},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify duration
        guest_token = response.data['data']['access_token']
        guest_session = GuestSession.objects.get(token=guest_token)
        duration = (guest_session.expires_at - guest_session.created_at).total_seconds() / 3600
        self.assertAlmostEqual(duration, 48, places=0)
    
    def test_guest_session_invalid_duration(self):
        """Test guest session fails with invalid duration"""
        response = self.client.post(
            self.guest_url,
            {'duration_hours': 200},  # More than max (168)
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


class UserProfileTestCase(APITestCase):
    """Integration tests for user profile endpoints"""
    
    def setUp(self):
        """Set up test client and test user"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        UserProfile.objects.create(user=self.user)
        
        self.profile_url = '/api/users/profile/'
        self.update_url = '/api/users/profile/update/'
        
        # Get JWT token
        login_response = self.client.post(
            '/api/users/auth/login/',
            {'username': 'testuser', 'password': 'TestPass123!'},
            format='json'
        )
        self.token = login_response.data['access']
    
    def test_get_profile_authenticated(self):
        """Test getting user profile with authentication"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['username'], 'testuser')
    
    def test_get_profile_unauthenticated(self):
        """Test getting profile fails without authentication"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_profile(self):
        """Test updating user profile"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.put(self.update_url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify update in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

