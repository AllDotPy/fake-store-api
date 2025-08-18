"""
Payment Configuration for Shop

This module contains configuration settings for payment processing.
"""

import os
from django.conf import settings

# Payment Provider Settings
PAYMENT_PROVIDERS = {
    'cinetpay': {
        'name': 'CinetPay',
        'api_url': os.getenv('CINETPAY_API_URL', 'https://api-checkout.cinetpay.com/v2'),
        'api_key': os.getenv('CINETPAY_API_KEY', ''),
        'secret_key': os.getenv('CINETPAY_SECRET_KEY', ''),
        'site_id': os.getenv('CINETPAY_SITE_ID', ''),
        'currency': 'XOF',
        'supported_methods': ['MOBILE_MONEY', 'CARD', 'BANK_TRANSFER']
    },
    'semoa': {
        'name': 'Semoa',
        'api_url': os.getenv('SEMOA_API_URL', 'https://api.semoa.com'),
        'api_key': os.getenv('SEMOA_API_KEY', ''),
        'secret_key': os.getenv('SEMOA_SECRET_KEY', ''),
        'merchant_id': os.getenv('SEMOA_MERCHANT_ID', ''),
        'currency': 'XOF',
        'supported_methods': ['MOBILE_MONEY', 'CARD']
    },
    'orange_money': {
        'name': 'Orange Money',
        'api_url': os.getenv('ORANGE_MONEY_API_URL', ''),
        'api_key': os.getenv('ORANGE_MONEY_API_KEY', ''),
        'secret_key': os.getenv('ORANGE_MONEY_SECRET_KEY', ''),
        'currency': 'XOF',
        'supported_methods': ['MOBILE_MONEY']
    },
    'moov_money': {
        'name': 'Moov Money',
        'api_url': os.getenv('MOOV_MONEY_API_URL', ''),
        'api_key': os.getenv('MOOV_MONEY_API_KEY', ''),
        'secret_key': os.getenv('MOOV_MONEY_SECRET_KEY', ''),
        'currency': 'XOF',
        'supported_methods': ['MOBILE_MONEY']
    }
}

# Default Payment Provider
DEFAULT_PAYMENT_PROVIDER = os.getenv('DEFAULT_PAYMENT_PROVIDER', 'cinetpay')

# Payment Settings
PAYMENT_SETTINGS = {
    'currency': 'XOF',
    'min_amount': 100,  # Minimum amount in cents
    'max_amount': 1000000,  # Maximum amount in cents
    'timeout': 30,  # Payment timeout in minutes
    'retry_attempts': 3,  # Number of retry attempts
    'webhook_timeout': 10,  # Webhook timeout in seconds
}

# Callback URLs
CALLBACK_URLS = {
    'success': os.getenv('PAYMENT_SUCCESS_URL', '/payment/success/'),
    'failure': os.getenv('PAYMENT_FAILURE_URL', '/payment/failure/'),
    'cancel': os.getenv('PAYMENT_CANCEL_URL', '/payment/cancel/'),
    'webhook': os.getenv('PAYMENT_WEBHOOK_URL', '/api/billings/webhook/'),
}

# Logging Configuration
PAYMENT_LOGGING = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'payment.log'
}

# Security Settings
PAYMENT_SECURITY = {
    'webhook_secret': os.getenv('PAYMENT_WEBHOOK_SECRET', ''),
    'ip_whitelist': os.getenv('PAYMENT_IP_WHITELIST', '').split(','),
    'require_signature': True,
}

def get_payment_provider_config(provider_name=None):
    """Get configuration for a specific payment provider."""
    provider = provider_name or DEFAULT_PAYMENT_PROVIDER
    return PAYMENT_PROVIDERS.get(provider, {})

def get_supported_providers():
    """Get list of supported payment providers."""
    return list(PAYMENT_PROVIDERS.keys())

def is_provider_supported(provider_name):
    """Check if a payment provider is supported."""
    return provider_name in PAYMENT_PROVIDERS

def get_payment_methods(provider_name=None):
    """Get supported payment methods for a provider."""
    provider_config = get_payment_provider_config(provider_name)
    return provider_config.get('supported_methods', []) 