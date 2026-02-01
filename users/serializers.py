from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import GuestSession, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for UserProfile model with proper field configurations.
    """
    class Meta:
        model = UserProfile
        fields = (
            'role', 'profile_picture', 'bio', 'phone_number', 
            'verified', 'two_factor_enabled', 'created_at', 
            'updated_at', 'last_login'
        )
        read_only_fields = ('role', 'verified', 'two_factor_enabled', 'created_at', 'updated_at', 'last_login')
        extra_kwargs = {
            'profile_picture': {'required': False},
            'bio': {'required': False},
            'phone_number': {'required': False},
        }


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True, required=False)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        return token

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        return token


class GuestSessionSerializer(serializers.ModelSerializer):
    access_token = serializers.CharField(source='token', read_only=True)
    expires_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = GuestSession
        fields = ('access_token', 'expires_at', 'id')
        read_only_fields = ('access_token', 'expires_at', 'id')
