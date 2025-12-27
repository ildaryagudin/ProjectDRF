from django.urls import path
from .views import (
    CreateCoursePaymentAPIView,
    PaymentStatusAPIView,
    StripeWebhookAPIView,
    UserPaymentsAPIView,
)

urlpatterns = [
    # Оплата курса
    path(
        'courses/<int:course_id>/pay/',
        CreateCoursePaymentAPIView.as_view(),
        name='create-course-payment'
    ),

    # Статус платежа
    path(
        'payments/<int:payment_id>/status/',
        PaymentStatusAPIView.as_view(),
        name='payment-status'
    ),

    # Мои платежи
    path(
        'my-payments/',
        UserPaymentsAPIView.as_view(),
        name='user-payments'
    ),

    # Вебхук Stripe (не требует аутентификации)
    path(
        'stripe/webhook/',
        StripeWebhookAPIView.as_view(),
        name='stripe-webhook'
    ),
]