from rest_framework import serializers
from .models import Course, Lesson
from .validators import YouTubeURLValidator, NoExternalLinksValidator


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lesson model."""

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'preview',
            'video_url', 'course', 'owner', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']
        validators = [
            NoExternalLinksValidator(fields=['description']),
        ]

    def validate_video_url(self, value):
        """Validate video URL using YouTubeURLValidator."""
        validator = YouTubeURLValidator()
        validator(value)
        return value

    def validate(self, data):
        """Additional validation for the entire serializer."""
        # Validate video_url if present
        if 'video_url' in data:
            validator = YouTubeURLValidator()
            validator(data['video_url'])

        # Validate description for external links
        if 'description' in data and data['description']:
            from .validators import validate_no_external_links
            validate_no_external_links(data['description'])

        return data


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
        validators = [
            NoExternalLinksValidator(fields=['description']),
        ]

    def get_lessons_count(self, obj):
        """Get count of lessons for the course."""
        return obj.lessons.count()

    def validate(self, data):
        """Validate description for external links."""
        if 'description' in data and data['description']:
            from .validators import validate_no_external_links
            validate_no_external_links(data['description'])

        return data


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
        validators = [
            NoExternalLinksValidator(fields=['description']),
        ]

    def get_lessons_count(self, obj):
        """Get count of lessons for the course."""
        return obj.lessons.count()

    def validate(self, data):
        """Validate description for external links."""
        if 'description' in data and data['description']:
            from .validators import validate_no_external_links
            validate_no_external_links(data['description'])

        return data



class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_email', 'course', 'course_title',
            'subscribed_at', 'is_active'
        ]
        read_only_fields = ['id', 'subscribed_at', 'is_active']


class CourseWithSubscriptionSerializer(CourseSerializer):
    """Serializer for Course with subscription status."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ['is_subscribed']

    def get_is_subscribed(self, obj):
        """Check if current user is subscribed to the course."""
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                course=obj,
                is_active=True
            ).exists()

        return False


class CourseListWithSubscriptionSerializer(CourseListSerializer):
    """Serializer for Course list with subscription status."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ['is_subscribed']

    def get_is_subscribed(self, obj):
        """Check if current user is subscribed to the course."""
        request = self.context.get('request')

        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                course=obj,
                is_active=True
            ).exists()

        return False