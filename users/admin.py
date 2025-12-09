from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Payment


class UserAdmin(BaseUserAdmin):
    """Define admin model for custom User model with no username field."""

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'phone', 'city', 'avatar')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payment model."""

    list_display = ('id', 'user', 'payment_date', 'course', 'lesson', 'amount', 'payment_method')
    list_filter = ('payment_date', 'payment_method', 'user')
    search_fields = ('user__email', 'user__first_name', 'user__last_name',
                     'course__title', 'lesson__title')
    date_hierarchy = 'payment_date'
    readonly_fields = ('payment_date',)

    fieldsets = (
        (_('User Information'), {
            'fields': ('user',)
        }),
        (_('Payment Details'), {
            'fields': ('payment_date', 'amount', 'payment_method')
        }),
        (_('Purchase'), {
            'fields': ('course', 'lesson'),
            'description': _('Select either a course or a lesson, not both.')
        }),
    )


admin.site.register(User, UserAdmin)