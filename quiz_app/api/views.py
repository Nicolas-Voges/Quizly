from rest_framework.views import APIView
from rest_framework.viewsets import generics
from rest_framework.response import Response
from rest_framework import status
from .serializers import QuizPostSerializer, QuizSerializer
from quiz_app.models import Quiz, Question
from pathlib import Path
import yt_dlp
import re
import os
import whisper
from google import genai
import json
from rest_framework.permissions import IsAuthenticated
from .permissions import IsCreator

class CreateQuizAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def download_audio(self, url, tmp_filename):
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": tmp_filename,
            "quiet": True,
            "noplaylist": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            return Response({"error": f"Error during download: {str(e)}"}, status=500)
        

    def transcribe_audio(self, tmp_filename):
        try:
            model = whisper.load_model("tiny", device="cuda" if os.getenv("WHISPER_USE_CUDA") == "1" else "cpu")
            result = model.transcribe(tmp_filename)
            return result["text"]
        except Exception as e:
            os.remove(tmp_filename)
            return Response({"error": f"Error during transcription: {str(e)}"}, status=500)
        

    def generate_quiz_json(self, transcript_text):
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

            prompt = f"""
            Based on the following transcript, generate a quiz in valid JSON format.

            The quiz must follow this exact structure:

            {{
              "title": "Create a concise quiz title based on the topic of the transcript.",
              "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
              "questions": [
                {{
                  "question_title": "The question goes here.",
                  "question_options": ["Option A", "Option B", "Option C", "Option D"],
                  "answer": "The correct answer from the above options"
                }},
                ...
                (exactly 10 questions)
              ]
            }}

            Requirements:
            - Each question must have exactly 4 distinct answer options.
            - Only one correct answer is allowed per question, and it must be present in 'question_options'.
            - The output must be valid JSON and parsable as-is (e.g., using Python's json.loads).
            - Do not include explanations, comments, or any text outside the JSON
            ---
            {transcript_text}
            ---
            """

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            raw_text = response.text
            cleaned_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text.strip(), flags=re.MULTILINE)
            return json.loads(cleaned_text)
        except Exception as e:
            return Response({"error": f"Fehler bei der Quiz-Erstellung: {str(e)}"}, status=500)
    

    def post(self, request):
        serializer = QuizPostSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        url = serializer.validated_data["url"]
        audio_path = Path(__file__).resolve().parent.parent.parent / 'media' / 'audio.m4a'

        if audio_path.exists():
            audio_path.unlink()

        tmp_filename = str(audio_path)

        self.download_audio(url, tmp_filename)

        transcript_text = self.transcribe_audio(tmp_filename)
        os.remove(tmp_filename)

        quiz_json = self.generate_quiz_json(transcript_text)

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
    permission_classes = [IsAuthenticated]
    serializer_class = QuizSerializer
    queryset = Quiz.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(creator=self.request.user)
   

class QuizRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsCreator]
    serializer_class = QuizSerializer
    queryset = Quiz.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(creator=self.request.user)
    

    def get_object(self):
        pk = self.kwargs.get("pk")
        obj = generics.get_object_or_404(Quiz, pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj