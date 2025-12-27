# payments/services.py

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError
from materials.models import Course, Lesson
from users.models import Payment as LocalPayment
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Настраиваем Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Сервис для работы с Stripe платежами"""

    @staticmethod
    def create_product(name, description=None, metadata=None):
        """
        Создать продукт в Stripe

        Args:
            name: Название продукта
            description: Описание продукта
            metadata: Дополнительные метаданные

        Returns:
            Объект продукта Stripe
        """
        try:
            product_data = {
                'name': name,
                'active': True,
            }

            if description:
                product_data['description'] = description

            if metadata:
                product_data['metadata'] = metadata

            product = stripe.Product.create(**product_data)
            logger.info(f"Продукт Stripe создан: {product.id}")
            return product

        except stripe.error.StripeError as e:
            logger.error(f"Ошибка создания продукта Stripe: {str(e)}")
            raise ValidationError(f"Ошибка платежного сервиса: {str(e)}")

    @staticmethod
    def create_price(product_id, unit_amount, currency='usd', recurring=False):
        """
        Создать цену в Stripe

        Args:
            product_id: ID продукта Stripe
            unit_amount: Цена в центах
            currency: Код валюты
            recurring: Является ли подпиской

        Returns:
            Объект цены Stripe
        """
        try:
            price_data = {
                'unit_amount': unit_amount,  # В центах
                'currency': currency,
                'product': product_id,
            }

            if recurring:
                price_data['recurring'] = {'interval': 'month'}

            price = stripe.Price.create(**price_data)
            logger.info(f"Цена Stripe создана: {price.id}")
            return price

        except stripe.error.StripeError as e:
            logger.error(f"Ошибка создания цены Stripe: {str(e)}")
            raise ValidationError(f"Ошибка платежного сервиса: {str(e)}")

    @staticmethod
    def create_checkout_session(price_id, success_url, cancel_url, metadata=None, customer_email=None):
        """
        Создать сессию оплаты в Stripe

        Args:
            price_id: ID цены Stripe
            success_url: URL для перенаправления после успешной оплаты
            cancel_url: URL для перенаправления при отмене оплаты
            metadata: Дополнительные метаданные
            customer_email: Email покупателя

        Returns:
            Объект сессии оплаты Stripe
        """
        try:
            session_data = {
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': price_id,
                    'quantity': 1,
                }],
                'mode': 'payment',
                'success_url': success_url,
                'cancel_url': cancel_url,
            }

            if metadata:
                session_data['metadata'] = metadata

            if customer_email:
                session_data['customer_email'] = customer_email

            checkout_session = stripe.checkout.Session.create(**session_data)
            logger.info(f"Сессия оплаты Stripe создана: {checkout_session.id}")
            return checkout_session

        except stripe.error.StripeError as e:
            logger.error(f"Ошибка создания сессии оплаты Stripe: {str(e)}")
            raise ValidationError(f"Ошибка платежного сервиса: {str(e)}")

    @staticmethod
    def retrieve_checkout_session(session_id):
        """
        Получить информацию о сессии оплаты

        Args:
            session_id: ID сессии оплаты

        Returns:
            Объект сессии оплаты Stripe
        """
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Ошибка получения сессии Stripe: {str(e)}")
            return None

    @staticmethod
    def create_course_payment(course, user, amount):
        """
        Создать процесс оплаты для курса

        Args:
            course: Объект курса
            user: Объект пользователя
            amount: Сумма в рублях/долларах

        Returns:
            dict: Словарь с ссылкой на оплату и информацией
        """
        try:
            # Конвертируем сумму в центы
            amount_cents = int(amount * 100)

            # 1. Создаем продукт в Stripe
            product = StripeService.create_product(
                name=f"Курс: {course.title}",
                description=course.description[:500] if course.description else None,
                metadata={
                    'course_id': str(course.id),
                    'type': 'course'
                }
            )

            # 2. Создаем цену в Stripe
            price = StripeService.create_price(
                product_id=product.id,
                unit_amount=amount_cents,
                currency=settings.STRIPE_CURRENCY
            )

            # 3. Создаем локальную запись платежа
            local_payment = LocalPayment.objects.create(
                user=user,
                course=course,
                amount=amount,
                payment_method='stripe',
                stripe_product_id=product.id,
                stripe_price_id=price.id,
                payment_date=None  # Обновим после успешной оплаты
            )

            # 4. Создаем сессию оплаты
            metadata = {
                'payment_id': str(local_payment.id),
                'course_id': str(course.id),
                'user_id': str(user.id),
                'type': 'course_payment'
            }

            checkout_session = StripeService.create_checkout_session(
                price_id=price.id,
                success_url=f"{settings.FRONTEND_SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_CANCEL_URL}?payment_id={local_payment.id}",
                metadata=metadata,
                customer_email=user.email
            )

            # 5. Обновляем локальную запись платежа
            local_payment.stripe_session_id = checkout_session.id
            local_payment.stripe_payment_url = checkout_session.url
            local_payment.save()

            return {
                'payment_id': local_payment.id,
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id,
                'amount': amount,
                'currency': settings.STRIPE_CURRENCY
            }

        except Exception as e:
            logger.error(f"Ошибка создания оплаты курса: {str(e)}")
            raise

    @staticmethod
    def handle_webhook_event(payload, sig_header):
        """
        Обработать событие вебхука Stripe

        Args:
            payload: Тело запроса
            sig_header: Заголовок с подписью

        Returns:
            bool: Успешно ли обработано событие
        """
        try:
            # Проверяем подпись вебхука
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )

            # Обрабатываем событие
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                return StripeService._handle_payment_success(session)

            elif event['type'] == 'checkout.session.expired':
                session = event['data']['object']
                return StripeService._handle_payment_expired(session)

            logger.info(f"Обработано событие Stripe: {event['type']}")
            return True

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Ошибка проверки подписи вебхука: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Ошибка обработки вебхука: {str(e)}")
            return False

    @staticmethod
    def _handle_payment_success(session):
        """Обработать успешную оплату"""
        try:
            metadata = session.get('metadata', {})
            payment_id = metadata.get('payment_id')

            if not payment_id:
                logger.error("Отсутствует payment_id в событии успешной оплаты")
                return False

            # Обновляем локальную запись платежа
            payment = LocalPayment.objects.get(id=payment_id)
            payment.payment_date = datetime.fromtimestamp(session['created'])
            payment.stripe_payment_intent = session.get('payment_intent')
            payment.stripe_payment_status = 'paid'
            payment.save()

            logger.info(f"Платеж обновлен как успешный: {payment_id}")
            return True

        except LocalPayment.DoesNotExist:
            logger.error(f"Запись платежа не найдена: {payment_id}")
            return False
        except Exception as e:
            logger.error(f"Ошибка обработки успешной оплаты: {str(e)}")
            return False