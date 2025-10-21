from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Quiz(models.Model):
    title = models.CharField(max_length=63)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    video_url = models.URLField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Quiz {self.id} {self.title}  by {self.creator.username}"
    

class Question(models.Model):
    question_title = models.CharField(max_length=255)
    question_options = models.JSONField()
    answer = models.CharField(max_length=255)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    
    def __str__(self):
        return f"Question {self.id} for Quiz {self.quiz.id}"