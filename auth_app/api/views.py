"""API views for authentication: register, login, token refresh and logout.

This module provides API endpoints used by the tests and the frontend
to register users, obtain JWT tokens, refresh access tokens and to
blacklist refresh tokens on logout.

The views intentionally keep behavior minimal and rely on
`rest_framework_simplejwt` for token management. Cookies are used to
store JWT tokens in HttpOnly cookies.
"""

from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from rest_framework_simplejwt.serializers import TokenBlacklistSerializer
from rest_framework.exceptions import AuthenticationFailed

from .serializers import RegistrationSerializer

class RegistrationAPIView(APIView):
    """Allow new users to register.

    POST: Create a new user account. Expects the serializer fields as
    defined in :class:`auth_app.api.serializers.RegistrationSerializer`.
    Returns a JSON object with a "detail" message on success or
    serializer errors with HTTP 400 on failure.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Handle POST requests to register a user."""
        serializer = RegistrationSerializer(data=request.data)

        data = {}
        if serializer.is_valid():
            serializer.save()
            data = {
                'detail': "User created successfully!"
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class LoginTokenObtainPairView(TokenObtainPairView):
    """Obtain JWT tokens and set them as HttpOnly cookies.

    On successful authentication the view sets two cookies
    (``access_token`` and ``refresh_token``) and returns a JSON object
    with a success message and basic user information.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Authenticate the user and return tokens as cookies."""
        response = super().post(request, *args, **kwargs)
        access = response.data.get('access', None)
        refresh = response.data.get('refresh', None)

        response.set_cookie(
            key='access_token',
            value=access,
            httponly=True,
            secure=True,
            samesite='Lax'
        )

        response.set_cookie(
            key='refresh_token',
            value=refresh,
            httponly=True,
            secure=True,
            samesite='Lax'
        )

        user = User.objects.get(username=request.data.get('username'))

        response.data = {
            'detail': "Login successfully!",
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }

        return response
    

class AccessTokenRefreshView(TokenRefreshView):
    """Refresh the access token using the refresh token stored in a cookie.

    The view reads the refresh token from the cookie ``refresh_token`` and
    returns a new access token in the response body and as an
    HttpOnly cookie. If the cookie is missing or invalid, the view
    returns HTTP 401.
    """

    def post(self, request, *args, **kwargs):
        """Handle POST to refresh the access token."""
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token is None:
            return Response(
                {'detail': 'Refresh token not provided.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = self.get_serializer(data={'refresh': refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {'detail': 'Invalid refresh token.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        access_token = serializer.validated_data.get('access')

        response = Response({'detail': "Token refreshed", 'access': access_token}, status=status.HTTP_200_OK)

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=True,
            samesite='Lax'
        )

        return response
    

class LogoutTokenBlacklistView(TokenBlacklistView):
    """Blacklist the refresh token stored in the cookie and clear cookies.

    This view overrides the serializer construction to pull the refresh
    token from the request cookies. After delegating to the parent
    class to blacklist the token, it deletes the token cookies and
    returns a friendly success message.
    """

    def get_serializer(self, *args, **kwargs):
        """Return a TokenBlacklistSerializer populated with the cookie token.

        Raises AuthenticationFailed if no refresh token cookie is present.
        """
        refresh_token = self.request.COOKIES.get('refresh_token')
        if refresh_token is None:
            raise AuthenticationFailed("Not authenticated.")
        kwargs['data'] = {'refresh': refresh_token}
        return TokenBlacklistSerializer(*args, **kwargs)


    def post(self, request, *args, **kwargs):
        """Blacklist the refresh token and clear auth cookies.

        Returns a 200 response with a confirmation message.
        """
        response = super().post(request, *args, **kwargs)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        response.data = {'detail': "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."}
        return response
