import os
from django.conf import settings

# Конфигурация Stripe API
STRIPE_API_KEY = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_ваш_тестовый_секретный_ключ')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_ваш_тестовый_публичный_ключ')

# Настройки оплаты
STRIPE_CURRENCY = 'usd'  # Валюта по умолчанию
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# URL для перенаправления после оплаты
FRONTEND_SUCCESS_URL = 'http://localhost:3000/payment/success/'
FRONTEND_CANCEL_URL = 'http://localhost:3000/payment/cancel/'