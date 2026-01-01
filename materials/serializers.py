from rest_framework import serializers
from .models import Course, Lesson
from .validators import YouTubeURLValidator, NoExternalLinksValidator
from .validators import validate_youtube_url  # Добавить импорт
from .models import Course, Lesson, Subscription
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer
from drf_spectacular.types import OpenApiTypes


class LessonSerializer(serializers.ModelSerializer):
    """Serializer for Lesson model."""

    video_url = serializers.URLField(validators=[validate_youtube_url])  # Добавить валидатор

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'preview',
            'video_url', 'course', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'video_url': {
                'help_text': 'Ссылка на видео YouTube (разрешены только ссылки на YouTube)'
            },
            'description': {
                'help_text': 'Описание урока (не может содержать внешние ссылки кроме YouTube)'
            }
        }

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

    lessons_count = serializers.IntegerField(
        source='lessons.count',
        read_only=True
    )
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()  # Добавить поле

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на курс."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                course=obj
            ).exists()
        return False

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'preview', 'description',
            'created_at', 'updated_at', 'lessons_count',
            'lessons', 'is_subscribed'  # Добавить is_subscribed
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'lessons_count', 'is_subscribed']



class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for Course list (without detailed lessons)."""

    lessons_count = serializers.IntegerField(
        source='lessons.count',
        read_only=True
    )
    is_subscribed = serializers.SerializerMethodField()  # Добавить поле

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на курс."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user,
                course=obj
            ).exists()
        return False

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'preview', 'description',
            'created_at', 'updated_at', 'lessons_count', 'is_subscribed'  # Добавить is_subscribed
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'lessons_count', 'is_subscribed']



class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for Subscription model."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = Subscription
        fields = ['id', 'user', 'course', 'created_at']
        read_only_fields = ['id', 'created_at']


@extend_schema_serializer(
    examples=[
        {
            'title': 'Python для начинающих',
            'description': 'Изучение Python с нуля',
            'preview': 'http://example.com/course.jpg',
            'owner': 1,
            'is_subscribed': True
        }
    ]
)
class CourseWithSubscriptionSerializer(CourseSerializer):
    """Serializer for Course with subscription status."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ['is_subscribed']

    @extend_schema_field(OpenApiTypes.BOOL)
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