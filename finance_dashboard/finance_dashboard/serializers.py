"""
Serializers for the users app.
"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, Role


class UserCreateSerializer(serializers.ModelSerializer):
    """Used by admins to create new users."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'role', 'is_active', 'password', 'password_confirm',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserDetailSerializer(serializers.ModelSerializer):
    """Read-only profile view."""
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'is_active', 'date_joined',
        ]
        read_only_fields = ['id', 'email', 'date_joined']


class UserUpdateSerializer(serializers.ModelSerializer):
    """Admin-level update: can change role, status, names."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'role', 'is_active']

    def validate_role(self, value):
        valid_roles = [r.value for r in Role]
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"Invalid role. Must be one of: {', '.join(valid_roles)}"
            )
        return value


class UserPasswordChangeSerializer(serializers.Serializer):
    """Allows an admin to reset another user's password."""
    new_password = serializers.CharField(validators=[validate_password])
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Enriches the JWT payload with role and user info."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = user.full_name
        return token

    def validate(self, attrs):
        # Block inactive users at login time
        data = super().validate(attrs)
        if not self.user.is_active:
            raise serializers.ValidationError(
                'This account is inactive. Contact an administrator.'
            )
        # Attach user profile to login response
        data['user'] = UserDetailSerializer(self.user).data
        return data