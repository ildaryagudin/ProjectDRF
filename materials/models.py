from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from urllib.parse import urlparse
import re


def validate_youtube_url_model(value):
    """Model-level validator for YouTube URLs."""
    if not value:
        return

    parsed_url = urlparse(value)
    domain = parsed_url.netloc.lower()

    # Check if domain is YouTube
    if 'youtube.com' not in domain and 'youtu.be' not in domain:
        raise ValidationError(
            _('Only YouTube URLs are allowed for video links.')
        )

    # Check for valid YouTube video ID
    youtube_regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(youtube_regex, value)

    if not match:
        raise ValidationError(
            _('Invalid YouTube URL format.')
        )


class Course(models.Model):
    """Course model."""

    title = models.CharField(
        _('title'),
        max_length=255,
        help_text=_('Course title')
    )
    preview = models.ImageField(
        _('preview image'),
        upload_to='courses/previews/',
        blank=True,
        null=True,
        help_text=_('Course preview image')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        null=True,
        help_text=_('Course description')
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name=_('owner')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('course')
        verbose_name_plural = _('courses')
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def clean(self):
        """Model-level validation."""
        from .validators import validate_no_external_links

        # Validate description for external links
        if self.description:
            try:
                validate_no_external_links(self.description)
            except ValidationError as e:
                raise ValidationError({'description': e.message})


class Lesson(models.Model):
    """Lesson model."""

    title = models.CharField(
        _('title'),
        max_length=255,
        help_text=_('Lesson title')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        null=True,
        help_text=_('Lesson description')
    )
    preview = models.ImageField(
        _('preview image'),
        upload_to='lessons/previews/',
        blank=True,
        null=True,
        help_text=_('Lesson preview image')
    )
    video_url = models.URLField(
        _('video URL'),
        max_length=500,
        help_text=_('URL to the lesson video'),
        validators=[validate_youtube_url_model]
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name=_('course'),
        help_text=_('Related course')
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons',
        verbose_name=_('owner')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('lesson')
        verbose_name_plural = _('lessons')
        ordering = ['created_at']

    def __str__(self):
        return self.title

    def clean(self):
        """Model-level validation."""
        from .validators import validate_no_external_links

        # Validate description for external links
        if self.description:
            try:
                validate_no_external_links(self.description)
            except ValidationError as e:
                raise ValidationError({'description': e.message})


class Subscription(models.Model):
    """Subscription model for course updates."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('user'),
        help_text=_('Subscribed user')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('course'),
        help_text=_('Subscribed course')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('subscription')
        verbose_name_plural = _('subscriptions')
        unique_together = ['user', 'course']  # Один пользователь может подписаться на курс только один раз
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.course.title}"

    def save(self, *args, **kwargs):
        """Override save to ensure unique subscription."""
        # Check if subscription already exists
        if self.pk is None:
            existing_subscription = Subscription.objects.filter(
                user=self.user,
                course=self.course
            ).first()

            if existing_subscription:
                # If exists and inactive, activate it
                if not existing_subscription.is_active:
                    existing_subscription.is_active = True
                    existing_subscription.save()
                    return
                else:
                    raise ValidationError(
                        _('Subscription already exists for this user and course.')
                    )

        super().save(*args, **kwargs)