from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Payment


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'password2',
            'first_name', 'last_name', 'phone', 'city'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


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
    """Сериализатор платежа"""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)

    # Поля Stripe
    stripe_payment_url = serializers.URLField(read_only=True)
    stripe_payment_status = serializers.CharField(read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    is_stripe_payment = serializers.BooleanField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'user_email', 'payment_date',
            'course', 'course_title', 'lesson', 'lesson_title',
            'amount', 'payment_method', 'is_paid', 'is_stripe_payment',
            'stripe_product_id', 'stripe_price_id', 'stripe_session_id',
            'stripe_payment_intent', 'stripe_payment_url', 'stripe_payment_status'
        ]
        read_only_fields = [
            'id', 'payment_date', 'user_email', 'course_title', 'lesson_title',
            'stripe_payment_url', 'stripe_payment_status', 'is_paid', 'is_stripe_payment'
        ]


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Serializer for Payment model with detailed information."""

    user = UserSerializer(read_only=True)

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