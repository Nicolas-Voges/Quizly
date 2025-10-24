"""Views for quiz-related API endpoints.

This module exposes an endpoint to create a quiz (from a YouTube
URL) and standard DRF generic views to list, retrieve, update and
delete quizzes that belong to the authenticated user.
"""

from rest_framework.views import APIView
from rest_framework.viewsets import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from quiz_app.models import Quiz, Question
from .serializers import QuizPostSerializer, QuizSerializer
from .permissions import IsCreator
from .utils import generate_quiz_json_from_url

class CreateQuizAPIView(APIView):
    """Create a quiz resource from a YouTube URL.

    The view downloads audio, transcribes it and constructs quiz
    content via a language model. Helper methods raise exceptions on
    failure and the view returns appropriate HTTP responses.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create the quiz resource and its related Question objects."""
        serializer = QuizPostSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        url = serializer.validated_data["url"]
        
        quiz_json = generate_quiz_json_from_url(url)

        quiz = Quiz.objects.create(
            title=quiz_json['title'],
            description=quiz_json['description'],
            video_url=url,
            creator=request.user
        )

        for question_data in quiz_json['questions']:
            Question.objects.create(
                question_title=question_data['question_title'],
                question_options=question_data['question_options'],
                answer=question_data['answer'],
                quiz=quiz
            )

        return Response(QuizPostSerializer(quiz).data, status=status.HTTP_201_CREATED)
    

class QuizListAPIView(generics.ListAPIView):
    """List quizzes for the authenticated user.

    GET: Return a list of quizzes owned by the requesting user. The
    view uses the default pagination and serialization defined by DRF and
    the local serializer class.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = QuizSerializer
    queryset = Quiz.objects.all()

    def get_queryset(self):
        """Return queryset filtered to the current user.

        Ensures users only see their own quizzes.
        """

        queryset = super().get_queryset()
        return queryset.filter(creator=self.request.user)
   

class QuizRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a quiz owned by the requester.

    GET: return quiz details
    PUT/PATCH: update quiz fields (only allowed for the creator)
    DELETE: remove the quiz (only allowed for the creator)

    Object-level permissions are enforced by :class:`IsCreator`.
    """

    permission_classes = [IsAuthenticated, IsCreator]
    serializer_class = QuizSerializer
    queryset = Quiz.objects.all()

    def get_queryset(self):
        """Return queryset limited to quizzes owned by the requester.

        Ensures object-level views operate only on the requesting user's
        quiz objects.
        """

        queryset = super().get_queryset()
        return queryset.filter(creator=self.request.user)
    

    def get_object(self):
        """Retrieve the object by primary key and enforce permissions.

        Uses ``get_object_or_404`` and then runs the usual DRF permission
        checks for object-level access.
        """

        pk = self.kwargs.get("pk")
        obj = generics.get_object_or_404(Quiz, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj