from rest_framework import serializers
from .models import User, Payment
from materials.serializers import CourseSerializer, LessonSerializer


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'phone', 'city', 'avatar', 'date_joined',
            'is_active', 'is_staff'
        ]
        read_only_fields = ['id', 'date_joined', 'is_active', 'is_staff']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'city', 'avatar'
        ]


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_email', 'payment_date',
            'course', 'course_title', 'lesson', 'lesson_title',
            'amount', 'payment_method'
        ]
        read_only_fields = ['id', 'payment_date', 'user_email',
                            'course_title', 'lesson_title']


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Serializer for Payment model with detailed information."""

    user = UserSerializer(read_only=True)
    course = CourseSerializer(read_only=True)
    lesson = LessonSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'payment_date',
            'course', 'lesson', 'amount', 'payment_method'
        ]
        read_only_fields = ['id', 'payment_date']


class UserWithPaymentsSerializer(serializers.ModelSerializer):
    """Serializer for User model with payment history."""

    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'phone', 'city', 'avatar', 'payments'
        ]
        read_only_fields = ['id', 'payments']