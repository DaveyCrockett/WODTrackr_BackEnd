from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
from datetime import timedelta


class UserProfile(models.Model):
    """
    Extended user profile with additional authentication and user metadata.
    """
    ROLE_CHOICES = [
        ('user', 'Regular User'),
        # ('coach', 'Coach'),
        ('admin', 'Administrator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Profile: {self.user.username}"


class UserSession(models.Model):
    """
    Tracks authenticated user sessions with device and location info.
    Allows users to manage active sessions and log out from specific devices.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=255, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-last_activity']
        verbose_name_plural = "User Sessions"
    
    def __str__(self):
        return f"Session: {self.user.username} - {self.device_name}"
    
    def is_valid(self):
        """Check if session is still active and not expired"""
        return self.is_active and timezone.now() < self.expires_at
    
    def logout(self):
        """Mark session as inactive"""
        self.is_active = False
        self.save()


class UserPreference(models.Model):
    """
    Stores user preferences for UI, notifications, and defaults.
    """
    UNIT_CHOICES = [
        ('lbs', 'Pounds'),
        ('kg', 'Kilograms'),
    ]

    TIME_FORMAT_CHOICES = [
        ('12h', '12-hour'),
        ('24h', '24-hour'),
    ]

    THEME_CHOICES = [
        ('system', 'System'),
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    preferred_units = models.CharField(max_length=3, choices=UNIT_CHOICES, default='lbs')
    time_format = models.CharField(max_length=3, choices=TIME_FORMAT_CHOICES, default='12h')
    notifications_email = models.BooleanField(default=True)
    notifications_push = models.BooleanField(default=True)
    reminder_time = models.TimeField(null=True, blank=True)
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='system')
    timezone = models.CharField(max_length=64, default='UTC')
    locale = models.CharField(max_length=16, default='en-US')
    public_profile = models.BooleanField(default=True)
    default_rest_timer_seconds = models.PositiveIntegerField(default=90)
    metric_rounding = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Preferences: {self.user.username}"


class GuestSession(models.Model):
    """
    Represents a guest session token for unauthenticated users.
    Guests get a limited access token without creating an account.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=255, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Guest Sessions"
    
    def __str__(self):
        return f"Guest Session {self.id} - Expires {self.expires_at}"
    
    def is_valid(self):
        """Check if the guest session is still valid"""
        return self.is_active and timezone.now() < self.expires_at
    
    @classmethod
    def create_session(cls, ip_address=None, user_agent=None, duration_hours=24):
        """Create a new guest session"""
        expires_at = timezone.now() + timedelta(hours=duration_hours)
        session = cls(
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        session.token = f"guest_{session.id}"
        session.save()
        return session


class LoginAttempt(models.Model):
    """
    Tracks login attempts for security monitoring and abuse prevention.
    """
    username = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{status} login attempt: {self.username} from {self.ip_address}"
