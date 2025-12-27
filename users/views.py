from django_filters import rest_framework as filters
from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Payment
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserProfileUpdateSerializer,
    PaymentSerializer,
    PaymentDetailSerializer,
    UserWithPaymentsSerializer
)
from .filters import PaymentFilter
from .permissions import IsOwnerOrModerator, IsModerator, IsNotModerator
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

@extend_schema_view(
    list=extend_schema(
        summary='Получить список пользователей',
        description='Получить список всех пользователей (требуется аутентификация)',
        tags=['Пользователи'],
        parameters=[
            OpenApiParameter(
                name='email',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Фильтр по email'
            ),
        ]
    ),
    retrieve=extend_schema(
        summary='Получить информацию о пользователе',
        description='Получить детальную информацию о конкретном пользователе',
        tags=['Пользователи']
    ),
    update=extend_schema(
        summary='Обновить пользователя',
        description='Обновить информацию о пользователе (только владелец или модератор)',
        tags=['Пользователи']
    ),
    partial_update=extend_schema(
        summary='Частично обновить пользователя',
        description='Частично обновить информацию о пользователе',
        tags=['Пользователи']
    ),
    destroy=extend_schema(
        summary='Удалить пользователя',
        description='Удалить пользователя (только администратор)',
        tags=['Пользователи']
    ),
)

class UserRegistrationAPIView(generics.CreateAPIView):
    """
    API endpoint for user registration.
    Open for everyone (no authentication required).
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

@extend_schema(
    summary='Выход из системы',
    description='Выход пользователя из системы с инвалидацией refresh токена',
    tags=['Пользователи'],
    request=OpenApiTypes.OBJECT,
    responses={
        205: 'Успешный выход',
        400: 'Неверный токен'
    },
    examples=[
        OpenApiExample(
            'Запрос на выход',
            value={'refresh_token': 'ваш_refresh_токен'}
        )
    ]
)

class UserLogoutAPIView(APIView):
    """
    API endpoint for user logout (blacklist refresh token).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing user instances.
    """
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'update_profile':
            return UserProfileUpdateSerializer
        elif self.action == 'profile_with_payments':
            return UserWithPaymentsSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'create':
            # Registration should be open for everyone
            permission_classes = [permissions.AllowAny]
        elif self.action in ['list', 'retrieve']:
            # Anyone can view user list and details
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Only owner or moderator can update/delete
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]
        else:
            # Default permission
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]


    @extend_schema(
        summary='Обновить профиль',
        description='Обновить профиль текущего пользователя',
        tags=['Пользователи'],
        request=UserProfileUpdateSerializer,
        responses={200: UserSerializer}
    )
    @action(detail=True, methods=['put', 'patch'], url_path='update-profile')

    def update_profile(self, request, pk=None):
        """Update user profile."""
        user = self.get_object()
        serializer = UserProfileUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    @extend_schema(
        summary='Мой профиль',
        description='Получить профиль текущего пользователя',
        tags=['Пользователи'],
        responses={200: UserSerializer}
    )
    @action(detail=False, methods=['get'], url_path='my-profile')

    def my_profile(self, request):
        """Get current user profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


    @extend_schema(
        summary='История платежей пользователя',
        description='Получить историю платежей конкретного пользователя',
        tags=['Пользователи', 'Платежи'],
        parameters=[
            OpenApiParameter(
                name='payment_method',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Фильтр по способу оплаты',
                enum=['cash', 'transfer']
            ),
        ]
    )
    @action(detail=True, methods=['get'], url_path='payments')

    def user_payments(self, request, pk=None):
        """Get payments history for specific user."""
        user = self.get_object()
        payments = user.payments.all()

        # Apply filtering
        filtered_payments = PaymentFilter(request.GET, queryset=payments).qs

        page = self.paginate_queryset(filtered_payments)
        if page is not None:
            serializer = PaymentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PaymentSerializer(filtered_payments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='profile-with-payments')

    def profile_with_payments(self, request, pk=None):
        """Get user profile with payment history."""
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary='Список платежей',
        description='Получить список всех платежей с поддержкой фильтрации и сортировки',
        tags=['Платежи'],
        parameters=[
            OpenApiParameter(
                name='course',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Фильтр по ID курса'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Сортировка, например: -payment_date (сначала новые)'
            ),
        ]
    ),
    retrieve=extend_schema(
        summary='Детали платежа',
        description='Получить детальную информацию о платеже',
        tags=['Платежи']
    ),
    create=extend_schema(
        summary='Создать платеж',
        description='Создать новый платеж (обычно используется через Stripe)',
        tags=['Платежи'],
        request=PaymentSerializer,
        responses={201: PaymentSerializer}
    ),
)

class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing payment instances.
    Supports filtering by date, course, lesson, and payment method.
    """
    queryset = Payment.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = PaymentFilter

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaymentDetailSerializer
        return PaymentSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsModerator]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Override to apply ordering by default."""
        queryset = super().get_queryset()
        # Default ordering: newest payments first
        if not self.request.GET.get('ordering'):
            queryset = queryset.order_by('-payment_date')
        return queryset

    @extend_schema(
        summary='Регистрация пользователя',
        description='Регистрация нового пользователя в системе',
        tags=['Пользователи'],
        request=UserRegistrationSerializer,
        responses={
            201: UserSerializer,
            400: 'Ошибка валидации'
        },
        examples=[
            OpenApiExample(
                'Успешная регистрация',
                value={
                    'email': 'user@example.com',
                    'password': 'password123',
                    'password2': 'password123',
                    'first_name': 'Иван',
                    'last_name': 'Иванов',
                    'phone': '+79991234567',
                    'city': 'Москва'
                }
            )
        ]
    )