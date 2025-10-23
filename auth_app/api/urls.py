"""URL patterns for the authentication API endpoints.

This module registers the login, refresh, registration and logout routes
used by the frontend and tests.
"""

from django.urls import path

from .views import (
    RegistrationAPIView,
    LoginTokenObtainPairView,
    AccessTokenRefreshView,
    LogoutTokenBlacklistView,
)

urlpatterns = [
    path('login/', LoginTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', AccessTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegistrationAPIView.as_view(), name='register'),
    path('logout/', LogoutTokenBlacklistView.as_view(), name='logout'),
]