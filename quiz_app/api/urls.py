from django.urls import path

from .views import CreateQuizAPIView

urlpatterns = [
    path('createQuiz/', CreateQuizAPIView.as_view(), name='create-quiz')
]