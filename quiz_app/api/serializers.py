from rest_framework import serializers

from quiz_app.models import Quiz, Question


class QuizPostSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    url = serializers.URLField(write_only=True)
    questions = QuestionSerializer(many=True, read_only=True)
    class Meta:
        model = Quiz
        fields = [
            'url',
            'id',
            'title',
            'description',
            'created_at',
            'updated_at',
            'video_url',
            'questions'
        ]
        read_only_fields = [
            'id',
            'title',
            'description',
            'created_at',
            'updated_at',
            'video_url',
            'questions'
        ]

    def format_datetime(self, dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(dt.microsecond / 1000):03d}Z"


    def get_created_at(self, obj):
        return self.format_datetime(obj.created_at)
    

    def get_updated_at(self, obj):
        return self.format_datetime(obj.updated_at)


    def validate_url(self, value):
        if "youtube.com" in value:
            return value
        elif "youtu.be" in value:
            video_id = value.split("youtu.be/")[-1].split("?")[0]
            return f"https://www.youtube.com/watch?v={video_id}"
        else:
            raise serializers.ValidationError("Invalid YouTube URL")