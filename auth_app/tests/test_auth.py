from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

class RegisterTests(APITestCase):

    def get_request_data(self, **overrides):
        base = {
            'username': "test_username",
            'password': "test_password",
            'confirmed_password': "test_password",
            'email': "test_email@example.com"
        }
        base.update(overrides)
        return base
    

    def setUp(self):
        self.username = 'test_user'
        self.email = 'test@user.de'
        self.User = get_user_model()
        self.url = reverse('register')
        self.user = self.User.objects.create_user(username=self.username, email=self.email, password='TEST1234')


    def test_post_success(self):
        expected_fields = {'detail'}
        response = self.client.post(self.url, self.get_request_data(), format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), expected_fields)
        self.assertTrue(self.User.objects.filter(username=self.get_request_data()['username']).exists())
        self.assertEqual(self.User.objects.filter(username=self.get_request_data()['username']).count(), 1)


    def test_post_fails(self):
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

    def setUp(self):
        self.username = 'test_user'
        self.password = 'test1234'
        self.User = get_user_model()
        self.user = self.User.objects.create_user(username=self.username, password=self.password)
        self.url = reverse('token_obtain_pair')

    def test_post_success(self):
        data = {
            'username': self.username,
            'password': self.password
        }
        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.cookies)
        self.assertIn('refresh', response.cookies)


    def test_post_fails(self):
        cases = [
            ("wrong_username", {'username': self.username, 'password': 'wrong_password'}),
            ("wrong_password", {'username': 'wrong', 'password': self.password})
        ]

        for message, data in cases:
            with self.subTest(test_case=message):
                response = self.client.post(self.url, data, format='json')

                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
                self.assertNotIn('access', response.cookies)
                self.assertNotIn('refresh', response.cookies)