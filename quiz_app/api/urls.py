from django.urls import path
from rest_framework import routers

from .views import CreateQuizAPIView, QuizListAPIView, QuizRetrieveUpdateDestroyAPIView
router = routers.DefaultRouter()
urlpatterns = [
    path('createQuiz/', CreateQuizAPIView.as_view(), name='create-quiz'),
    path('quizzes/', QuizListAPIView.as_view(), name='quizzes-list'),
    path('quizzes/<int:pk>/', QuizRetrieveUpdateDestroyAPIView.as_view(), name='quizzes-detail')
]