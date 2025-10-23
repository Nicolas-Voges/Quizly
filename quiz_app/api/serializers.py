"""Serializers for the quiz app API.

Provide serializers for Question and Quiz models and a specialized
serializer used when creating quizzes from a YouTube URL.
"""

from rest_framework import serializers

from quiz_app.models import Quiz, Question


class QuestionSerializer(serializers.ModelSerializer):
    """Serialize Question instances including formatted timestamps."""

    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ['id', 'question_title', 'question_options', 'answer', 'created_at', 'updated_at']

    def format_datetime(self, dt):
        """Return a string representation of ``dt`` with millisecond precision.

        Args:
            dt (datetime): The datetime to format.

        Returns:
            str: Formatted datetime like 'YYYY-MM-DDTHH:MM:SS.mmmZ'.
        """
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(dt.microsecond / 1000):03d}Z"


    def get_created_at(self, obj):
        """Return the formatted creation timestamp for the object."""
        return self.format_datetime(obj.created_at)


    def get_updated_at(self, obj):
        """Return the formatted update timestamp for the object."""
        return self.format_datetime(obj.updated_at)


class QuizPostSerializer(serializers.ModelSerializer):
    """Serializer used when creating a quiz from a YouTube URL.

    The serializer accepts a write-only ``url`` field and exposes the
    generated quiz fields as read-only.
    """

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
        """Format a datetime value for API output."""
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(dt.microsecond / 1000):03d}Z"


    def get_created_at(self, obj):
        """Return formatted created_at timestamp."""
        return self.format_datetime(obj.created_at)


    def get_updated_at(self, obj):
        """Return formatted updated_at timestamp."""
        return self.format_datetime(obj.updated_at)


    def validate_url(self, value):
        """Normalize YouTube short URLs to full watch URLs.

        Raises a ValidationError for unsupported URL formats.
        """
        if "youtube.com" in value:
            return value
        if "youtu.be" in value:
            video_id = value.split("youtu.be/")[-1].split("?")[0]
            return f"https://www.youtube.com/watch?v={video_id}"
        raise serializers.ValidationError("Invalid YouTube URL")


class QuizSerializer(serializers.ModelSerializer):
    """Serializer for read/update/delete operations on Quiz instances."""

    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = [
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
            'created_at',
            'updated_at',
            'video_url',
            'questions'
        ]


    def format_datetime(self, dt):
        """Format datetime values consistently for API output."""
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(dt.microsecond / 1000):03d}Z"


    def get_created_at(self, obj):
        """Return formatted created_at timestamp."""
        return self.format_datetime(obj.created_at)


    def get_updated_at(self, obj):
        """Return formatted updated_at timestamp."""
        return self.format_datetime(obj.updated_at)


    def update(self, instance, validated_data):
        """Update mutable fields of a Quiz instance and persist changes."""
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.save()
        return instance