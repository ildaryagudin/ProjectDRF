from rest_framework import serializers
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lesson model."""

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'preview',
            'video_url', 'course', 'owner', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model."""

    # Используем SerializerMethodField для количества уроков
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'preview', 'description', 'owner',
            'created_at', 'updated_at', 'lessons_count', 'lessons'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at', 'lessons_count']

    def get_lessons_count(self, obj):
        """Get count of lessons for the course."""
        return obj.lessons.count()


class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for Course list (without detailed lessons)."""

    # Используем SerializerMethodField для количества уроков
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'preview', 'description', 'owner',
            'created_at', 'updated_at', 'lessons_count'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at', 'lessons_count']

    def get_lessons_count(self, obj):
        """Get count of lessons for the course."""
        return obj.lessons.count()