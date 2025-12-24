from django.contrib import admin
from .models import Course, Lesson
from django.contrib import admin
from .models import Course, Lesson, Subscription

class LessonInline(admin.TabularInline):
    """Inline for lessons in course admin."""
    model = Lesson
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin interface for Course model."""
    list_display = ('title', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """Admin interface for Lesson model."""
    list_display = ('title', 'course', 'created_at')
    list_filter = ('course', 'created_at')
    search_fields = ('title', 'description', 'video_url')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for Subscription model."""
    list_display = ('user', 'course', 'is_active', 'subscribed_at')
    list_filter = ('is_active', 'subscribed_at', 'course')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'course__title')
    readonly_fields = ('subscribed_at',)
    list_editable = ('is_active',)

    fieldsets = (
        (None, {
            'fields': ('user', 'course', 'is_active')
        }),
        (_('Timestamps'), {
            'fields': ('subscribed_at',),
            'classes': ('collapse',)
        }),
    )