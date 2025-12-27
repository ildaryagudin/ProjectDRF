from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with email as the unique identifier."""

    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(_('phone'), max_length=15, blank=True, null=True)
    city = models.CharField(_('city'), max_length=100, blank=True, null=True)
    avatar = models.ImageField(
        _('avatar'),
        upload_to='users/avatars/',
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email


class Payment(models.Model):
    """Модель платежа"""

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Наличные')
        TRANSFER = 'transfer', _('Банковский перевод')
        STRIPE = 'stripe', _('Оплата через Stripe')

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Пользователь')
    )
    payment_date = models.DateTimeField(
        _('Дата оплаты'),
        null=True,
        blank=True
    )
    course = models.ForeignKey(
        'materials.Course',
        on_delete=models.SET_NULL,
        related_name='payments',
        verbose_name=_('Оплаченный курс'),
        blank=True,
        null=True
    )
    lesson = models.ForeignKey(
        'materials.Lesson',
        on_delete=models.SET_NULL,
        related_name='payments',
        verbose_name=_('Оплаченный урок'),
        blank=True,
        null=True
    )
    amount = models.DecimalField(
        _('Сумма'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Сумма оплаты')
    )
    payment_method = models.CharField(
        _('Способ оплаты'),
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )

    # Поля для интеграции со Stripe
    stripe_product_id = models.CharField(
        _('ID продукта Stripe'),
        max_length=100,
        blank=True,
        null=True
    )
    stripe_price_id = models.CharField(
        _('ID цены Stripe'),
        max_length=100,
        blank=True,
        null=True
    )
    stripe_session_id = models.CharField(
        _('ID сессии Stripe'),
        max_length=100,
        blank=True,
        null=True
    )
    stripe_payment_intent = models.CharField(
        _('Payment Intent Stripe'),
        max_length=100,
        blank=True,
        null=True
    )
    stripe_payment_url = models.URLField(
        _('URL оплаты Stripe'),
        max_length=500,
        blank=True,
        null=True
    )
    stripe_payment_status = models.CharField(
        _('Статус оплаты Stripe'),
        max_length=50,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _('Платеж')
        verbose_name_plural = _('Платежи')
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.user.email} - {self.amount} - {self.get_payment_method_display()}"

    @property
    def is_stripe_payment(self):
        """Является ли платежом через Stripe"""
        return self.payment_method == self.PaymentMethod.STRIPE

    @property
    def is_paid(self):
        """Оплачен ли платеж"""
        return self.payment_date is not None

    def mark_as_paid(self, payment_date=None):
        """Пометить как оплаченный"""
        from django.utils import timezone
        self.payment_date = payment_date or timezone.now()
        self.save()

    def clean(self):
        """Validate that either course or lesson is set, but not both."""
        from django.core.exceptions import ValidationError

        if not self.course and not self.lesson:
            raise ValidationError(_('Either course or lesson must be set.'))
        if self.course and self.lesson:
            raise ValidationError(_('Cannot set both course and lesson.'))

    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.clean()
        super().save(*args, **kwargs)