"""Serializers for authentication-related API endpoints.

This module provides a serializer for user registration used by the
registration API. It performs basic validation and creates a new
User instance when saved.
"""

from rest_framework import serializers
from django.contrib.auth.models import User


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer used to register a new user.

    Validation ensures that the password and confirmed_password match
    and that the email address is unique among existing users.
    """

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirmed_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'email': {
                'required': True
            }
        }


    def validate_confirmed_password(self, value):
        """Ensure the password confirmation matches the password."""

        password = self.initial_data.get('password')
        if password and value and password != value:
            raise serializers.ValidationError('Passwords do not match')
        return value


    def validate_email(self, value):
        """Validate that the email address is not already in use."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value


    def save(self):
        """Create and return a new User instance with the validated data."""
        pw = self.validated_data['password']

        account = User(email=self.validated_data['email'], username=self.validated_data['username'])
        account.set_password(pw)
        account.save()
        return account