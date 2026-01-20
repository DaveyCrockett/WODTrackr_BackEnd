from django.test import TestCase
from django.contrib.auth.models import User
from users.models import UserProfile
from users.serializers import UserSerializer, UserProfileSerializer
from django.utils import timezone


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
        
        # Non-read-only field should be updated
        self.assertEqual(self.user_profile.role, 'admin')
    
    def test_profile_serializer_optional_fields(self):
        """Test that optional fields can be omitted"""
        data = {
            'role': 'coach'
        }
        serializer = UserProfileSerializer(data=data)
        # Should be valid even without profile_picture, bio, and phone_number
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
    
    def test_user_serializer_all_fields(self):
        """Test that UserSerializer contains all expected user fields"""
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        
        expected_fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']
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

