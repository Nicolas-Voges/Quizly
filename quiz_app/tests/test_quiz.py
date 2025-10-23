from unittest.mock import patch
from anyio import Path
from pathlib import Path
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from quiz_app.models import Quiz, Question

User = get_user_model()

class QuizTests(APITestCase):


    def get_url_detail(self, pk):
        return reverse('quizzes-detail', kwargs={'pk': pk})


    def setUp(self):
        self.video_url = "https://www.youtube.com/watch?v=_dQYvRM9zNY"
        self.video_url_2 = "https://youtu.be/_dQYvRM9zNY?si=mCT_gsc0qQmdgPpp"
        self.post_data = {'url': self.video_url}
        self.post_data_2 = {'url': self.video_url_2}
        self.user = User.objects.create_user(username="username", email="te@st.mail", password='TEST1234')
        self.user_2 = User.objects.create_user(username="username", email="te@st.mail_2", password='TEST1234')
        self.quiz = Quiz.objects.create(
            title="Sample Quiz",
            description="A simple quiz for testing.",
            created_at=timezone.now(),
            updated_at=timezone.now(),
            video_url=self.video_url,
            creator=self.user
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
        self.expected_fields = {'id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions'}


    def login(self, user=None):
        if user is None:
            user = self.user
        login_response = self.client.post(self.url_login, {'username': user.username, 'password': 'TEST1234'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + login_response.cookies.get('access_token').value)


    def tearDown(self):
        audio_path = Path(settings.BASE_DIR) / 'media' / 'audio.m4a'
        if audio_path.exists():
            audio_path.unlink()


    @patch('quiz_app.api.views.CreateQuizAPIView.download_audio')
    @patch('quiz_app.api.views.CreateQuizAPIView.transcribe_audio')
    @patch('quiz_app.api.views.CreateQuizAPIView.generate_quiz_json')
    def test_post_success(self, mock_generate_quiz_json, mock_transcribe_audio, mock_download_audio):
        mock_download_audio.return_value = None
        mock_download_audio.side_effect = lambda url, filename: open(filename, 'wb').close()
        mock_transcribe_audio.return_value = {"text": "Sample transcript text."}
        mock_generate_quiz_json.return_value = {
            "title": "Sample Quiz Title",
            "description": "Sample Quiz Description",
            "questions": [
                {
                    "question_title": "Sample Question",
                    "question_options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                    "answer": "Option 1"
                }
            ]
        }
        for post_data in [self.post_data, self.post_data_2]:
            self.login()
            response = self.client.post(self.url_create, post_data, format='json')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(set(response.data.keys()), self.expected_fields)


    def test_post_fails(self):
        data = {"video_url": "invalid_url"}

        response = self.client.post(self.url_create, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.login()
        response = self.client.post(self.url_create, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_get_list_success(self):
        self.login()
        response = self.client.get(self.url_list, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        for quiz in response.data:
            self.assertEqual(set(quiz.keys()), self.expected_fields)
            self.assertEqual(quiz['creator'], self.user.id)


    def test_get_list_fails(self):
        response = self.client.get(self.url_list, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def test_get_detail_success(self):
        self.login()
        response = self.client.get(self.get_url_detail(self.quiz.pk), format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data.keys()), self.expected_fields)
        self.assertEqual(response.data['id'], self.quiz.id)
        self.assertEqual(response.data['title'], self.quiz.title)
        self.assertEqual(response.data['description'], self.quiz.description)
        self.assertEqual(response.data['video_url'], self.quiz.video_url)
        self.assertEqual(len(response.data['questions']), len(self.questions))


    def test_get_detail_fails(self):
        cases = [
            ('non-existent quiz', self.user, 9999, status.HTTP_404_NOT_FOUND),
            ('unauthenticated access', None, self.quiz.pk, status.HTTP_401_UNAUTHORIZED),
            ('access by non-creator', self.user_2, self.quiz.pk, status.HTTP_403_FORBIDDEN)
        ]

        for desc, login, pk, status_code in cases:
            if login:
                self.login(user=login)
            response = self.client.get(self.get_url_detail(pk), format='json')

            self.assertEqual(response.status_code, status_code, msg=f"Failed on case: {desc}")


    def test_patch_detail_success(self):
        self.login()
        updated_data = {
            "title": "Updated Quiz Title",
            "description": "Updated Quiz Description"
        }
        response = self.client.patch(self.get_url_detail(self.quiz.pk), updated_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], updated_data['title'])
        self.assertEqual(response.data['description'], updated_data['description'])


    def test_patch_detail_fails(self):
        cases = [
            ('invalid data', self.user, self.quiz.pk, {"title": ""}, status.HTTP_400_BAD_REQUEST),
            ('unauthenticated access', None, self.quiz.pk, {"title": "New Title"}, status.HTTP_401_UNAUTHORIZED),
            ('access by non-creator', self.user_2, self.quiz.pk, {"title": "New Title"}, status.HTTP_403_FORBIDDEN),
            ('non-existent quiz', self.user, 9999, {"title": "New Title"}, status.HTTP_404_NOT_FOUND)
        ]

        for desc, login, pk, data, status_code in cases:
            if login:
                self.login(user=login)
            response = self.client.patch(self.get_url_detail(pk), data, format='json')

            self.assertEqual(response.status_code, status_code, msg=f"Failed on case: {desc}")


    def test_delete_detail(self):
        cases = [
            ('unauthenticated access', None, status.HTTP_401_UNAUTHORIZED),
            ('access by non-creator', self.user_2, status.HTTP_403_FORBIDDEN),
            ('successful deletion', self.user, status.HTTP_204_NO_CONTENT),
            ('deletion of non-existent quiz', self.user, status.HTTP_404_NOT_FOUND)
        ]
        for desc, login, status_code in cases:
            if login:
                self.login(user=login)
            response = self.client.delete(self.get_url_detail(self.quiz.pk), format='json')

            self.assertEqual(response.status_code, status_code, msg=f"Failed on case: {desc}")