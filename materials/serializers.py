from rest_framework import serializers
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lesson model."""

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'preview',
            'video_url', 'course', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model."""

    lessons_count = serializers.IntegerField(
        source='lessons.count',
        read_only=True
    )
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'preview', 'description',
            'created_at', 'updated_at', 'lessons_count', 'lessons'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'lessons_count']


class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for Course list (without detailed lessons)."""

    lessons_count = serializers.IntegerField(
        source='lessons.count',
        read_only=True
    )

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'preview', 'description',
            'created_at', 'updated_at', 'lessons_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'lessons_count']