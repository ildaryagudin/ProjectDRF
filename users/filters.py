from django_filters import rest_framework as filters
from .models import Payment


class PaymentFilter(filters.FilterSet):
    """FilterSet for Payment model."""

    payment_date_from = filters.DateFilter(
        field_name='payment_date',
        lookup_expr='gte',
        label='Payment date from (YYYY-MM-DD)'
    )
    payment_date_to = filters.DateFilter(
        field_name='payment_date',
        lookup_expr='lte',
        label='Payment date to (YYYY-MM-DD)'
    )
    course = filters.NumberFilter(
        field_name='course__id',
        label='Course ID'
    )
    lesson = filters.NumberFilter(
        field_name='lesson__id',
        label='Lesson ID'
    )
    payment_method = filters.ChoiceFilter(
        choices=Payment.PaymentMethod.choices,
        label='Payment method'
    )
    user_email = filters.CharFilter(
        field_name='user__email',
        lookup_expr='icontains',
        label='User email contains'
    )

    ordering = filters.OrderingFilter(
        fields=(
            ('payment_date', 'payment_date'),
            ('amount', 'amount'),
        ),
        field_labels={
            'payment_date': 'Payment date',
            'amount': 'Amount',
        }
    )

    class Meta:
        model = Payment
        fields = [
            'payment_date_from', 'payment_date_to',
            'course', 'lesson', 'payment_method', 'user_email'
        ]