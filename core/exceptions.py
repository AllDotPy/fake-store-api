"""
Custom exceptions for Fake Shop API.

This module provides a base exception class and various specialized exceptions
for handling different types of errors in the application.
"""

from rest_framework.exceptions import APIException
from rest_framework import status
from django.utils.translation import gettext_lazy as _


class FakeShopBaseException(APIException):
    """
    Base exception class for all Fake Shop application exceptions.
    
    Inherits from rest_framework.exceptions.APIException and adds
    additional fields such as error_code for better error handling.
    """
    
    def __init__(self, detail=None, code=None, status_code=None, **kwargs):
        """
        Initialize the exception.
        
        Args:
            detail: Error message or description
            code: Custom error code for the exception
            status_code: HTTP status code (defaults to 500)
            **kwargs: Additional fields to include in the exception
        """
        self.error_code = code or self.__class__.__name__
        self.status_code = status_code or getattr(self, 'default_status_code', status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.additional_fields = kwargs
        
        super().__init__(detail=detail, code=self.status_code)
    
    def get_full_details(self):
        """Get complete exception details including error code and additional fields."""
        details = {
            'error_code': self.error_code,
            'message': self.detail,
            'status_code': self.status_code,
        }
        details.update(self.additional_fields)
        return details


# Payment Related Exceptions
class PaymentError(FakeShopBaseException):
    """Base exception for all payment-related errors."""
    default_status_code = status.HTTP_400_BAD_REQUEST


class PaymentInitiationError(PaymentError):
    """Raised when payment initiation fails."""
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Failed to initiate payment"),
            code="PAYMENT_INITIATION_ERROR",
            **kwargs
        )


class PaymentProcessingError(PaymentError):
    """Raised when payment processing fails."""
    default_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Payment processing failed"),
            code="PAYMENT_PROCESSING_ERROR",
            **kwargs
        )


class PaymentValidationError(PaymentError):
    """Raised when payment validation fails."""
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Payment validation failed"),
            code="PAYMENT_VALIDATION_ERROR",
            **kwargs
        )


class PaymentRefundError(PaymentError):
    """Raised when payment refund fails."""
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Payment refund failed"),
            code="PAYMENT_REFUND_ERROR",
            **kwargs
        )


class PaymentWebhookError(PaymentError):
    """Raised when payment webhook processing fails."""
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Payment webhook processing failed"),
            code="PAYMENT_WEBHOOK_ERROR",
            **kwargs
        )


class InsufficientFundsError(PaymentError):
    """Raised when there are insufficient funds for payment."""
    default_status_code = status.HTTP_402_PAYMENT_REQUIRED
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Insufficient funds for payment"),
            code="INSUFFICIENT_FUNDS",
            **kwargs
        )


class PaymentMethodNotSupportedError(PaymentError):
    """Raised when the payment method is not supported."""
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Payment method not supported"),
            code="PAYMENT_METHOD_NOT_SUPPORTED",
            **kwargs
        )


# Network Related Exceptions
class NetworkError(FakeShopBaseException):
    """Base exception for all network-related errors."""
    default_status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class ConnectionTimeoutError(NetworkError):
    """Raised when a network connection times out."""
    default_status_code = status.HTTP_504_GATEWAY_TIMEOUT
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Network connection timeout"),
            code="CONNECTION_TIMEOUT",
            **kwargs
        )


class ServiceUnavailableError(NetworkError):
    """Raised when an external service is unavailable."""
    default_status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Service temporarily unavailable"),
            code="SERVICE_UNAVAILABLE",
            **kwargs
        )


class APIError(NetworkError):
    """Raised when an external API call fails."""
    default_status_code = status.HTTP_502_BAD_GATEWAY
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("External API error"),
            code="API_ERROR",
            **kwargs
        )


# Command Related Exceptions
class CommandError(FakeShopBaseException):
    """Base exception for all command-related errors."""
    default_status_code = status.HTTP_400_BAD_REQUEST


class CommandCancellationError(CommandError):
    """Raised when a command is cancelled."""
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Command was cancelled"),
            code="COMMAND_CANCELLATION_ERROR",
            **kwargs
        )


class CommandExecutionError(CommandError):
    """Raised when command execution fails."""
    default_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Command execution failed"),
            code="COMMAND_EXECUTION_ERROR",
            **kwargs
        )


class CommandValidationError(CommandError):
    """Raised when command validation fails."""
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Command validation failed"),
            code="COMMAND_VALIDATION_ERROR",
            **kwargs
        )


# Business Logic Exceptions
class BusinessLogicError(FakeShopBaseException):
    """Base exception for all business logic errors."""
    default_status_code = status.HTTP_400_BAD_REQUEST


class OrderError(BusinessLogicError):
    """Base exception for all order-related errors."""
    default_status_code = status.HTTP_400_BAD_REQUEST


class OrderNotFoundError(OrderError):
    """Raised when an order is not found."""
    default_status_code = status.HTTP_404_NOT_FOUND
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Order not found"),
            code="ORDER_NOT_FOUND",
            **kwargs
        )


class OrderValidationError(OrderError):
    """Raised when order validation fails."""
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Order validation failed"),
            code="ORDER_VALIDATION_ERROR",
            **kwargs
        )


class ProductError(BusinessLogicError):
    """Base exception for all product-related errors."""
    default_status_code = status.HTTP_400_BAD_REQUEST


class ProductNotFoundError(ProductError):
    """Raised when a product is not found."""
    default_status_code = status.HTTP_404_NOT_FOUND
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Product not found"),
            code="PRODUCT_NOT_FOUND",
            **kwargs
        )


class ProductOutOfStockError(ProductError):
    """Raised when a product is out of stock."""
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Product is out of stock"),
            code="PRODUCT_OUT_OF_STOCK",
            **kwargs
        )


class CategoryError(BusinessLogicError):
    """Base exception for all category-related errors."""
    default_status_code = status.HTTP_400_BAD_REQUEST


class CategoryNotFoundError(CategoryError):
    """Raised when a category is not found."""
    default_status_code = status.HTTP_404_NOT_FOUND
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Category not found"),
            code="CATEGORY_NOT_FOUND",
            **kwargs
        )


class NotificationError(BusinessLogicError):
    """Base exception for all notification-related errors."""
    default_status_code = status.HTTP_400_BAD_REQUEST


class NotificationNotFoundError(NotificationError):
    """Raised when a notification is not found."""
    default_status_code = status.HTTP_404_NOT_FOUND
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Notification not found"),
            code="NOTIFICATION_NOT_FOUND",
            **kwargs
        )


class NotificationServiceError(NotificationError):
    """Raised when notification service operations fail."""
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Notification service error"),
            code="NOTIFICATION_SERVICE_ERROR",
            **kwargs
        )


class UserError(BusinessLogicError):
    """Base exception for all user-related errors."""
    default_status_code = status.HTTP_400_BAD_REQUEST


class UserNotFoundError(UserError):
    """Raised when a user is not found."""
    default_status_code = status.HTTP_404_NOT_FOUND
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("User not found"),
            code="USER_NOT_FOUND",
            **kwargs
        )


class UserAuthenticationError(UserError):
    """Raised when user authentication fails."""
    default_status_code = status.HTTP_401_UNAUTHORIZED
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Authentication failed"),
            code="USER_AUTHENTICATION_ERROR",
            **kwargs
        )


class UserAuthorizationError(UserError):
    """Raised when user authorization fails."""
    default_status_code = status.HTTP_403_FORBIDDEN
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Access denied"),
            code="USER_AUTHORIZATION_ERROR",
            **kwargs
        )


# Data Related Exceptions
class DataError(FakeShopBaseException):
    """Base exception for all data-related errors."""
    default_status_code = status.HTTP_400_BAD_REQUEST


class DataValidationError(DataError):
    """Raised when data validation fails."""
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Data validation failed"),
            code="DATA_VALIDATION_ERROR",
            **kwargs
        )


class DataNotFoundError(DataError):
    """Raised when requested data is not found."""
    default_status_code = status.HTTP_404_NOT_FOUND
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Data not found"),
            code="DATA_NOT_FOUND",
            **kwargs
        )


class DataIntegrityError(DataError):
    """Raised when data integrity is violated."""
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Data integrity error"),
            code="DATA_INTEGRITY_ERROR",
            **kwargs
        )


# Configuration Related Exceptions
class ConfigurationError(FakeShopBaseException):
    """Raised when there's a configuration error."""
    default_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Configuration error"),
            code="CONFIGURATION_ERROR",
            **kwargs
        )


# Security Related Exceptions
class SecurityError(FakeShopBaseException):
    """Base exception for all security-related errors."""
    default_status_code = status.HTTP_403_FORBIDDEN


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""
    default_status_code = status.HTTP_401_UNAUTHORIZED
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Authentication failed"),
            code="AUTHENTICATION_ERROR",
            **kwargs
        )


class AuthorizationError(SecurityError):
    """Raised when authorization fails."""
    default_status_code = status.HTTP_403_FORBIDDEN
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Access denied"),
            code="AUTHORIZATION_ERROR",
            **kwargs
        )


class TokenError(SecurityError):
    """Raised when token-related operations fail."""
    default_status_code = status.HTTP_401_UNAUTHORIZED
    
    def __init__(self, detail=None, **kwargs):
        super().__init__(
            detail=detail or _("Token error"),
            code="TOKEN_ERROR",
            **kwargs
        ) 