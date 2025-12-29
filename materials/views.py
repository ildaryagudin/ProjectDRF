from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Course, Subscription
from .serializers import SubscriptionSerializer
from .paginators import CoursePagination, LessonPagination
from .paginators import MaterialsPagination
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from django.utils import timezone
from datetime import timedelta
from tasks.tasks import send_course_update_notification


class SubscriptionAPIView(APIView):
    """
    API endpoint for managing course subscriptions.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Toggle subscription for a course.
        """
        user = request.user
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {"error": "course_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if subscription exists
        subscription = Subscription.objects.filter(
            user=user,
            course=course
        ).first()

        if subscription:
            # Toggle subscription status
            subscription.is_active = not subscription.is_active
            subscription.save()

            if subscription.is_active:
                message = 'Subscription activated'
            else:
                message = 'Subscription deactivated'
        else:
            # Create new subscription
            subscription = Subscription.objects.create(
                user=user,
                course=course
            )
            message = 'Subscription created'

        serializer = SubscriptionSerializer(subscription)
        return Response(
            {
                "message": message,
                "subscription": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def delete(self, request, *args, **kwargs):
        """
        Remove subscription for a course.
        """
        user = request.user
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {"error": "course_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription = get_object_or_404(
            Subscription,
            user=user,
            course_id=course_id
        )

        subscription.delete()

        return Response(
            {"message": "Subscription removed"},
            status=status.HTTP_204_NO_CONTENT
        )

    def get(self, request, *args, **kwargs):
        """
        Get user's subscriptions.
        """
        user = request.user
        subscriptions = Subscription.objects.filter(user=user, is_active=True)

        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)


class CourseSubscriptionStatusAPIView(APIView):
    """
    API endpoint for checking subscription status for a course.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id, *args, **kwargs):
        """
        Check if user is subscribed to a course.
        """
        user = request.user

        is_subscribed = Subscription.objects.filter(
            user=user,
            course_id=course_id,
            is_active=True
        ).exists()

        return Response({"is_subscribed": is_subscribed})


@extend_schema_view(
    list=extend_schema(
        summary='Список курсов',
        description='Получить список всех курсов (пользователи видят только свои курсы, модераторы - все)',
        tags=['Курсы'],
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Номер страницы'
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Количество элементов на странице'
            ),
        ]
    ),
    retrieve=extend_schema(
        summary='Детали курса',
        description='Получить детальную информацию о курсе, включая список уроков и статус подписки',
        tags=['Курсы']
    ),
    create=extend_schema(
        summary='Создать курс',
        description='Создать новый курс (обычные пользователи могут создавать, модераторы - нет)',
        tags=['Курсы'],
        request=CourseSerializer,
        responses={
            201: CourseSerializer,
            403: 'Недостаточно прав (модераторы не могут создавать курсы)'
        }
    ),
    update=extend_schema(
        summary='Обновить курс',
        description='Обновить информацию о курсе (владелец или модератор)',
        tags=['Курсы']
    ),
    destroy=extend_schema(
        summary='Удалить курс',
        description='Удалить курс (только владелец, модераторы не могут удалять)',
        tags=['Курсы']
    ),
)

class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Course model with CRUD operations.
    """
    queryset = Course.objects.all()
    permission_classes = [permissions.AllowAny]  # Для тестирования
    pagination_class = MaterialsPagination

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseSerializer

        @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
        @extend_schema(
            summary='Подписчики курса',
            description='Получить список подписчиков курса (владелец или модератор)',
            tags=['Курсы', 'Подписки'],
            responses={
                200: SubscriptionSerializer(many=True),
                403: 'Недостаточно прав'
            }
        )


        def subscribe(self, request, pk=None):
        """Подписка/отписка на обновления курса."""
        course = self.get_object()
        user = request.user

        if not user.is_authenticated:
            return Response(
                {'error': 'Требуется аутентификация'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if request.method == 'POST':
            # Подписка
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                course=course
            )
            if created:
                return Response(
                    {'message': 'Вы успешно подписались на обновления курса'},
                    status=status.HTTP_201_CREATED
                )
            return Response(
                {'message': 'Вы уже подписаны на этот курс'},
                status=status.HTTP_200_OK
            )

        elif request.method == 'DELETE':
            # Отписка
            subscription = Subscription.objects.filter(
                user=user,
                course=course
            ).first()
            if subscription:
                subscription.delete()
                return Response(
                    {'message': 'Вы отписались от обновлений курса'},
                    status=status.HTTP_200_OK
                )
            return Response(
                {'message': 'Вы не подписаны на этот курс'},
                status=status.HTTP_404_NOT_FOUND
            )

    def update(self, request, *args, **kwargs):
        """Переопределяем update для отправки уведомлений"""
        # Проверяем, когда курс обновлялся в последний раз
        course = self.get_object()
        last_update = course.updated_at

        # Вызываем родительский метод
        response = super().update(request, *args, **kwargs)

        # Проверяем, прошло ли более 4 часов с последнего обновления
        time_threshold = timezone.now() - timedelta(hours=4)

        if last_update < time_threshold:
            # Отправляем уведомления асинхронно
            send_course_update_notification.delay(
                course_id=course.id,
                update_type='course'
            )
            logger.info(f"Запущена задача отправки уведомлений для курса {course.id}")

        return response

@extend_schema(
    summary='Список уроков / Создать урок',
    description='Получить список уроков или создать новый урок',
    tags=['Уроки'],
    parameters=[
        OpenApiParameter(
            name='page',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Номер страницы'
        ),
    ],
    request=LessonSerializer,
    responses={
        200: LessonSerializer(many=True),
        201: LessonSerializer
    }
)

class LessonListCreateAPIView(generics.ListCreateAPIView):
    """
    Generic view for listing and creating lessons.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = MaterialsPagination  # Добавляем пагинацию

class SubscriptionAPIView(APIView):
    """
    API endpoint for managing course subscriptions.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination  # Для GET запросов

    def get(self, request, *args, **kwargs):
        """
        Get user's subscriptions with pagination.
        """
        user = request.user
        subscriptions = Subscription.objects.filter(user=user, is_active=True)

        # Apply pagination
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = SubscriptionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

@extend_schema(
    summary='Проверить статус подписки',
    description='Проверить, подписан ли текущий пользователь на указанный курс',
    tags=['Подписки'],
    responses={200: OpenApiTypes.OBJECT}
)

@extend_schema(
    summary='Детали урока / Обновить / Удалить',
    description='Получить, обновить или удалить урок',
    tags=['Уроки'],
    methods=['GET', 'PUT', 'PATCH', 'DELETE'],
    responses={
        200: LessonSerializer,
        204: 'Урок успешно удален',
        403: 'Недостаточно прав'
    }
)

class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Generic view for retrieving, updating and deleting a lesson.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.AllowAny]

    def update(self, request, *args, **kwargs):
        """Переопределяем update для отправки уведомлений при обновлении урока"""
        # Получаем урок и его курс
        lesson = self.get_object()
        course = lesson.course
        last_update = course.updated_at

        # Вызываем родительский метод
        response = super().update(request, *args, **kwargs)

        # Проверяем, прошло ли более 4 часов с последнего обновления курса
        time_threshold = timezone.now() - timedelta(hours=4)

        if last_update < time_threshold:
            # Обновляем время изменения курса
            course.updated_at = timezone.now()
            course.save(update_fields=['updated_at'])

            # Отправляем уведомления асинхронно
            send_course_update_notification.delay(
                course_id=course.id,
                update_type='lesson'
            )
            logger.info(f"Запущена задача отправки уведомлений для курса {course.id} (обновлен урок)")

        return response

@extend_schema(
    summary='Управление подписками',
    description='Подписаться на курс, отписаться или получить список подписок',
    tags=['Подписки'],
    methods=['GET', 'POST', 'DELETE'],
    request=OpenApiTypes.OBJECT,
    responses={
        200: 'Операция выполнена успешно',
        201: SubscriptionSerializer
    },
    examples=[
        OpenApiExample(
            'Запрос на подписку/отписку',
            value={'course_id': 1},
            description='POST: переключить статус подписки, DELETE: удалить подписку'
        )
    ]
)