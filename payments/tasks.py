# payments/tasks.py

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

from users.models import Payment

logger = logging.getLogger(__name__)


@shared_task(queue='emails')
def send_payment_reminders():
    """
    Отправка напоминаний о предстоящих платежах (для подписок)
    """
    try:
        logger.info("Начинаем отправку напоминаний о платежах...")

        # В будущем можно добавить логику для подписок

        logger.info("Завершена отправка напоминаний о платежах")

    except Exception as e:
        logger.error(f"Ошибка при отправке напоминаний: {str(e)}")