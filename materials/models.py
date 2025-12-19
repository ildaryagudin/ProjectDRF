from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


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
        help_text=_('URL to the lesson video')
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