from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from quiz_app.models import Quiz, Question

User = get_user_model()

class QuizTests(APITestCase):


    def setUp(self):
        self.video_url = "https://www.youtube.com/watch?v=P8zzrqLEvoI"
        self.video_url_2 = "https://youtu.be/P8zzrqLEvoI?si=TsYQwovhCbhqNkr7"
        self.post_data = {'video_url': self.video_url}
        self.post_data_2 = {'video_url': self.video_url_2}
        self.user = User.objects.create_user(username="username", email="te@st.mail", password='TEST1234')
        self.quiz = Quiz.objects.create(
            title="Sample Quiz",
            description="A simple quiz for testing.",
            created_at=timezone.now(),
            updated_at=timezone.now(),
            video_url=self.video_url,
            creator=self.user.pk
        )
        self.questions = [
            Question.objects.create(
                question_title=f"Sample Question {i+1}",
                question_options=["Option 1", "Option 2", "Option 3", "Option 4"],
                answer="Option 1",
                quiz_id=self.quiz.pk
            )
            for i in range(10)
        ]
        self.url_login = reverse('token_obtain_pair')
        self.url_list = reverse('quizzes-list')
        self.url_create = reverse('create-quiz')
        self.url_detail = reverse('quizzes-detail', kwargs={'pk': self.quiz.pk})
        self.expected_fields = {'id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions'}

    def test_post_success(self):
        for post_data in [self.post_data, self.post_data_2]:
            self.client.post(self.url_login, {'username': 'username', 'password': 'TEST1234'}, format='json')
            response = self.client.post(self.url_create, post_data, format='json')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(set(response.data.keys()), self.expected_fields)


    def test_post_fails(self):
        data = {"video_url": "invalid_url"}

        response = self.client.post(self.url_create, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.post(self.url_login, {'username': 'username', 'password': 'TEST1234'}, format='json')
        response = self.client.post(self.url_create, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)