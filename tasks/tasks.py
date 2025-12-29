# tasks/tasks.py

from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

from materials.models import Course, Subscription
from users.models import User

logger = logging.getLogger(__name__)


@shared_task(queue='emails', bind=True, max_retries=3)
def send_course_update_notification(self, course_id, update_type='course'):
    """
    Отправка уведомления об обновлении курса подписчикам

    Args:
        course_id: ID курса
        update_type: Тип обновления ('course' или 'lesson')
    """
    try:
        logger.info(f"Начинаем отправку уведомлений для курса {course_id}")

        # Получаем курс
        course = Course.objects.get(id=course_id)

        # Проверяем, нужно ли отправлять уведомление
        if not course.should_send_notification():
            logger.info(f"Уведомление для курса {course_id} не требуется (отправлялось менее 4 часов назад)")
            return

        # Получаем всех активных подписчиков курса
        subscriptions = Subscription.objects.filter(
            course=course,
            is_active=True
        ).select_related('user')

        logger.info(f"Найдено {subscriptions.count()} подписчиков курса {course.title}")

        if not subscriptions.exists():
            logger.info(f"Нет активных подписчиков для курса {course.title}")
            return

        # Подготовка данных для email
        subject = f'Обновление курса: {course.title}'

        for subscription in subscriptions:
            try:
                user = subscription.user

                # Создаем HTML содержание письма
                context = {
                    'user_name': user.first_name or user.email,
                    'course_title': course.title,
                    'course_description': course.description[
                                          :200] + '...' if course.description else 'Описание отсутствует',
                    'update_type': 'курса' if update_type == 'course' else 'урока',
                    'site_url': 'http://localhost:8000',  # В продакшене заменить на реальный URL
                    'course_url': f'http://localhost:8000/api/courses/{course.id}/',
                    'unsubscribe_url': f'http://localhost:8000/api/subscriptions/{course.id}/status/',
                }

                html_content = render_to_string('emails/course_update_notification.html', context)
                text_content = strip_tags(html_content)

                # Отправляем email
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email],
                    reply_to=[settings.DEFAULT_FROM_EMAIL],
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)

                logger.info(f"Уведомление отправлено пользователю {user.email}")

            except Exception as e:
                logger.error(f"Ошибка отправки уведомления пользователю {user.email}: {str(e)}")
                # Продолжаем отправку другим пользователям

        logger.info(f"Завершена отправка уведомлений для курса {course.title}")

    except Course.DoesNotExist:
        logger.error(f"Курс с ID {course_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений: {str(e)}")
        # Повторная попытка через 5 минут
        raise self.retry(exc=e, countdown=300)


@shared_task(queue='emails')
def send_welcome_email(user_id):
    """Отправка приветственного письма новому пользователю"""
    try:
        user = User.objects.get(id=user_id)

        subject = 'Добро пожаловать в нашу образовательную платформу!'

        context = {
            'user_name': user.first_name or user.email,
            'site_url': 'http://localhost:8000',
        }

        html_content = render_to_string('emails/welcome_email.html', context)
        text_content = strip_tags(html_content)

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )

        logger.info(f"Приветственное письмо отправлено пользователю {user.email}")

    except User.DoesNotExist:
        logger.error(f"Пользователь с ID {user_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка отправки приветственного письма: {str(e)}")


@shared_task(queue='emails')
def send_payment_confirmation(payment_id):
    """Отправка подтверждения оплаты"""
    try:
        from users.models import Payment

        payment = Payment.objects.get(id=payment_id)
        user = payment.user

        subject = 'Подтверждение оплаты'

        # Определяем, что было оплачено
        if payment.course:
            item_name = payment.course.title
            item_type = 'курс'
        elif payment.lesson:
            item_name = payment.lesson.title
            item_type = 'урок'
        else:
            item_name = 'Неизвестный продукт'
            item_type = 'продукт'

        context = {
            'user_name': user.first_name or user.email,
            'item_name': item_name,
            'item_type': item_type,
            'amount': payment.amount,
            'payment_date': payment.payment_date,
            'payment_method': payment.get_payment_method_display(),
        }

        html_content = render_to_string('emails/payment_confirmation.html', context)
        text_content = strip_tags(html_content)

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )

        logger.info(f"Подтверждение оплаты отправлено пользователю {user.email}")

    except Exception as e:
        logger.error(f"Ошибка отправки подтверждения оплаты: {str(e)}")


# tasks/tasks.py

@shared_task(queue='emails')
def send_user_warning_email(user_id, days_left):
    """
    Отправка предупреждения пользователю о скорой блокировке
    """
    try:
        user = User.objects.get(id=user_id)

        subject = f'Ваш аккаунт будет заблокирован через {days_left} дней'

        context = {
            'user_name': user.first_name or user.email,
            'days_left': days_left,
            'last_login': user.last_login.strftime('%d.%m.%Y %H:%M') if user.last_login else 'никогда',
            'login_url': 'http://localhost:8000/api/token/',
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }

        html_content = render_to_string('emails/user_warning.html', context)
        text_content = strip_tags(html_content)

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )

        logger.info(f"Предупреждение о блокировке отправлено пользователю {user.email}")

    except User.DoesNotExist:
        logger.error(f"Пользователь с ID {user_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка отправки предупреждения: {str(e)}")


@shared_task(queue='emails')
def send_user_blocked_notification(user_id):
    """
    Отправка уведомления о блокировке аккаунта
    """
    try:
        user = User.objects.get(id=user_id)

        subject = 'Ваш аккаунт заблокирован'

        context = {
            'user_name': user.first_name or user.email,
            'last_login': user.last_login.strftime('%d.%m.%Y %H:%M') if user.last_login else 'никогда',
            'support_email': settings.DEFAULT_FROM_EMAIL,
            'unblock_url': 'http://localhost:8000/api/users/unblock-request/',
        }

        html_content = render_to_string('emails/user_blocked.html', context)
        text_content = strip_tags(html_content)

        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )

        logger.info(f"Уведомление о блокировке отправлено пользователю {user.email}")

    except Exception as e:
        logger.error(f"Ошибка отправки уведомления о блокировке: {str(e)}")