from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

from materials.models import Course, Lesson
from users.models import Payment
from users.serializers import PaymentSerializer
from .services import StripeService
import logging

logger = logging.getLogger(__name__)


class CreateCoursePaymentAPIView(APIView):
    """Создание оплаты курса"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Оплатить курс',
        description='Создать ссылку на оплату курса через Stripe',
        tags=['Платежи'],
        parameters=[
            OpenApiParameter(
                name='course_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID курса'
            ),
            OpenApiParameter(
                name='amount',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Сумма оплаты',
                required=False
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description='Ссылка на оплату создана'
            ),
            400: OpenApiResponse(description='Неверные параметры'),
            404: OpenApiResponse(description='Курс не найден'),
        }
    )
    def post(self, request, course_id):
        """Создать оплату курса"""
        try:
            # Получаем курс
            course = get_object_or_404(Course, id=course_id)

            # Получаем сумму оплаты
            amount = request.query_params.get('amount')
            if not amount:
                amount = 2990.00  # Дефолтная цена курса
            else:
                amount = float(amount)

            # Проверяем, не оплачен ли уже курс
            existing_payment = Payment.objects.filter(
                user=request.user,
                course=course,
                payment_date__isnull=False
            ).first()

            if existing_payment:
                return Response({
                    'message': 'Вы уже приобрели этот курс',
                    'payment_id': existing_payment.id,
                    'is_paid': True
                }, status=status.HTTP_200_OK)

            # Создаем оплату через Stripe
            result = StripeService.create_course_payment(
                course=course,
                user=request.user,
                amount=amount
            )

            return Response({
                'message': 'Ссылка на оплату создана',
                'data': result,
                'instructions': 'Используйте checkout_url для оплаты'
            }, status=status.HTTP_200_OK)

        except ValueError:
            return Response(
                {'error': 'Неверный формат суммы'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Ошибка создания оплаты курса: {str(e)}")
            return Response(
                {'error': 'Не удалось создать оплату, попробуйте позже'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PaymentStatusAPIView(APIView):
    """Проверка статуса оплаты"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Статус оплаты',
        description='Проверить статус оплаты',
        tags=['Платежи'],
        parameters=[
            OpenApiParameter(
                name='payment_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='ID платежа'
            ),
        ],
        responses={
            200: PaymentSerializer,
            403: OpenApiResponse(description='Нет доступа к этому платежу'),
            404: OpenApiResponse(description='Платеж не найден'),
        }
    )
    def get(self, request, payment_id):
        """Проверить статус оплаты"""
        try:
            # Получаем платеж (только свои)
            payment = get_object_or_404(Payment, id=payment_id)

            # Проверяем права доступа
            if payment.user != request.user and not request.user.is_staff:
                return Response(
                    {'error': 'Нет доступа к этому платежу'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Если это платеж через Stripe, обновляем статус
            if payment.is_stripe_payment and payment.stripe_session_id:
                session = StripeService.retrieve_checkout_session(
                    payment.stripe_session_id
                )
                if session:
                    payment.stripe_payment_status = session.get('payment_status')
                    payment.save()

            serializer = PaymentSerializer(payment)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Ошибка проверки статуса оплаты: {str(e)}")
            return Response(
                {'error': 'Не удалось проверить статус оплаты'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StripeWebhookAPIView(APIView):
    """Обработчик вебхуков Stripe"""

    permission_classes = []  # Не требует аутентификации

    @extend_schema(
        summary='Вебхук Stripe',
        description='Эндпоинт для получения вебхуков от Stripe (внутренний)',
        tags=['Платежи'],
        exclude=True  # Исключаем из документации
    )
    def post(self, request):
        """Обработать вебхук от Stripe"""
        try:
            payload = request.body
            sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

            if not sig_header:
                return Response(
                    {'error': 'Отсутствует заголовок подписи'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Обрабатываем вебхук
            success = StripeService.handle_webhook_event(payload, sig_header)

            if success:
                return Response({'status': 'success'})
            else:
                return Response(
                    {'error': 'Ошибка обработки вебхука'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Ошибка обработки вебхука: {str(e)}")
            return Response(
                {'error': 'Внутренняя ошибка сервера'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserPaymentsAPIView(APIView):
    """История платежей пользователя"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Мои платежи',
        description='Получить историю платежей текущего пользователя',
        tags=['Платежи'],
        responses={
            200: PaymentSerializer(many=True),
        }
    )
    def get(self, request):
        """Получить историю платежей"""
        payments = Payment.objects.filter(user=request.user).order_by('-payment_date')
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)