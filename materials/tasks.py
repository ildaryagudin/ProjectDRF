# materials/tasks.py

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

from materials.models import Course, Subscription
from users.models import User

logger = logging.getLogger(__name__)


@shared_task(queue='emails')
def send_course_statistics():
    """
    Отправка еженедельной статистики по курсам владельцам курсов
    """
    try:
        logger.info("Начинаем отправку еженедельной статистики...")

        # Находим все курсы
        courses = Course.objects.all()

        for course in courses:
            try:
                # Получаем владельца курса
                owner = course.owner
                if not owner or not owner.email:
                    continue

                # Собираем статистику
                total_subscribers = Subscription.objects.filter(
                    course=course,
                    is_active=True
                ).count()

                new_subscribers_last_week = Subscription.objects.filter(
                    course=course,
                    is_active=True,
                    subscribed_at__gte=timezone.now() - timedelta(days=7)
                ).count()

                # Создаем email
                subject = f'Еженедельная статистика курса: {course.title}'

                context = {
                    'course_title': course.title,
                    'total_subscribers': total_subscribers,
                    'new_subscribers': new_subscribers_last_week,
                    'course_url': f'http://localhost:8000/api/courses/{course.id}/',
                    'date_range': f"{(timezone.now() - timedelta(days=7)).strftime('%d.%m.%Y')} - {timezone.now().strftime('%d.%m.%Y')}",
                }

                html_content = render_to_string('emails/course_statistics.html', context)
                text_content = strip_tags(html_content)

                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[owner.email],
                    html_message=html_content,
                    fail_silently=False,
                )

                logger.info(f"Статистика отправлена владельцу курса {course.title}")

            except Exception as e:
                logger.error(f"Ошибка отправки статистики для курса {course.title}: {str(e)}")

        logger.info("Завершена отправка еженедельной статистики")

    except Exception as e:
        logger.error(f"Ошибка при отправке статистики: {str(e)}")