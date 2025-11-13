"""Tests for authentication API endpoints.

These tests cover registration, login, token refresh and logout
behavior as used by the project. The tests use DRF's
APITestCase to interact with the API like a client.
"""

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase


class RegisterTests(APITestCase):
    """Test cases for the registration endpoint.

    Methods in this class exercise successful registration and common
    failure cases (duplicate username/email and password mismatch).
    """

    def get_request_data(self, **overrides):
        """Return a complete registration payload with optional overrides.

        The returned dict contains default values and applies any
        overrides provided as keyword arguments.
        """
        base = {
            'username': "test_username",
            'password': "test_password",
            'confirmed_password': "test_password",
            'email': "test_email@example.com"
        }
        base.update(overrides)
        return base


    def setUp(self):
        """Create a user that can be used to test duplicate checks."""
        self.username = 'test_user'
        self.email = 'test@user.de'
        self.User = get_user_model()
        self.url = reverse('register')
        self.user = self.User.objects.create_user(username=self.username, email=self.email, password='TEST1234')


    def test_post_success(self):
        """Registration with valid data returns HTTP 201 and a detail field."""
        expected_fields = {'detail'}
        response = self.client.post(self.url, self.get_request_data(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), expected_fields)
        self.assertTrue(self.User.objects.filter(username=self.get_request_data()['username']).exists())
        self.assertEqual(self.User.objects.filter(username=self.get_request_data()['username']).count(), 1)


    def test_post_fails(self):
        """Common invalid registration payloads should return HTTP 400."""
        cases = [
            ("duplicate_username", self.get_request_data(username=self.username)),
            ("duplicate_email", self.get_request_data(email=self.email)),
            ("password_mismatch", self.get_request_data(confirmed_password="wrong"))
        ]

        for message, data in cases:
            with self.subTest(test_case=message):
                response = self.client.post(self.url, data, format='json')

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    """Tests for token obtain (login) behavior and cookie setting."""

    def setUp(self):
        """Create a user and set the login URL for the tests."""
        self.username = 'test_user'
        self.password = 'test1234'
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username=self.username, password=self.password)
        self.url = reverse('token_obtain_pair')


    def test_post_success(self):
        """Correct credentials result in cookies being set for tokens."""
        data = {
            'username': self.username,
            'password': self.password
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)


    def test_post_fails(self):
        """Invalid credentials must not set token cookies and return 401."""
        cases = [
            ("wrong_password", {'username': self.username, 'password': 'wrong_password'}),
            ("wrong_username", {'username': 'wrong', 'password': self.password})
        ]

        for message, data in cases:
            with self.subTest(test_case=message):
                response = self.client.post(self.url, data, format='json')

                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
                self.assertNotIn('access_token', response.cookies)
                self.assertNotIn('refresh_token', response.cookies)


class TokenRefreshTests(APITestCase):
    """Tests for refreshing the access token using the refresh cookie."""

    def setUp(self):
        self.username = 'test_user'
        self.password = 'test1234'
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username=self.username, password=self.password)
        self.login_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')


    def test_post_success(self):
        """A logged-in client can refresh the access token successfully."""
        self.client.post(self.login_url, {'username': self.username, 'password': self.password}, format='json')

        response = self.client.post(self.refresh_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


    def test_post_fails_no_cookie(self):
        """If no refresh cookie is present, the view returns 401."""
        response = self.client.post(self.refresh_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Refresh token not provided.')


    def test_post_fails_invalid_token(self):
        """An invalid refresh cookie yields an unauthorized response."""
        self.client.cookies['refresh_token'] = 'invalid_token'
        response = self.client.post(self.refresh_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Invalid refresh token.')


class LogoutTests(APITestCase):
    """Tests for logout and token blacklisting endpoint."""

    def setUp(self):
        self.username = 'test_user'
        self.password = 'test1234'
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username=self.username, password=self.password)
        self.login_url = reverse('token_obtain_pair')
        self.logout_url = reverse('logout')


    def test_post_success(self):
        """A logged-in client is logged out and cookies are cleared."""
        self.client.post(self.login_url, {'username': self.username, 'password': self.password}, format='json')

        response = self.client.post(self.logout_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies['access_token'].value, '')
        self.assertEqual(response.cookies['refresh_token'].value, '')


    def test_post_fails_no_cookie(self):
        response = self.client.post(self.logout_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)