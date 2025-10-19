from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

class RegisterTests(APITestCase):

    def get_request_data(self, **overrides):
        base = {
            "username": "test_username",
            "password": "test_password",
            "confirmed_password": "test_password",
            "email": "test_email@example.com"
        }
        base.update(overrides)
        return base
    

    def setUp(self):
        self.username = 'TEST_USER'
        self.email = 'TEST@USER.de'
        self.User = get_user_model()
        self.request_data = self.get_request_data()
        self.request_data_wrong_password = self.get_request_data(confirmed_password='wrong')
        self.request_data_wrong_email = self.get_request_data(email=self.email)
        self.request_data_wrong_username = self.get_request_data(username=self.username)
        self.url = reverse('register')
        self.user = self.User.objects.create_user(username=self.username, email=self.email, password='TEST1234')


    def test_post_success(self):
        expected_fields = {'detail'}
        response = self.client.post(self.url, self.request_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(set(response.data.keys()), expected_fields)


    def test_post_fails(self):
        cases = [
            self.request_data_wrong_username,
            self.request_data_wrong_email,
            self.request_data_wrong_password,
        ]

        for data in cases:
            response = self.client.post(self.url, data, format='json')

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)