import asyncio
import logging
from typing import Any, Dict, Optional, Union
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from easyswitch.types import TransactionStatus as EasySwitchTransactionStatus
from easyswitch import (
    EasySwitch, 
    TransactionDetail, 
    Provider,
    WebhookEvent,
)

from apps.billings.models import Transaction as T
from core.exceptions import (
    PaymentProcessingError,
    PaymentValidationError,
    PaymentWebhookError,
    ConfigurationError,
    TransactionNotFoundError
)

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Professional payment service using EasySwitch provider.
    
    This service handles all payment-related operations including:
    - Transaction creation and processing
    - Payment status verification
    - Provider integration management
    """
    
    def __init__(self, client=None):
        """
        Initialize the payment service.
        
        Args:
            client: Optional EasySwitch client instance for testing
        """
        try:
            env_file = settings.BASE_DIR / '.env'
            self._client = client or self._get_client(env_file)
            
            self._validate_client_configuration()
        except Exception as e:
            logger.error(f"Failed to initialize EasySwitch client: {str(e)}")
            raise ConfigurationError(
                detail=f"Payment service configuration failed. EasySwitch client initialization error: {str(e)}",
            )

    def _get_client(self, env_file: str=None):
        config = {
            "debug": True,
            "providers": {
                Provider.FEDAPAY: {
                    "api_secret": settings.EASYSWITCH_FEDAPAY_SECRET_KEY,
                    "callback_url": settings.EASYSWITCH_FEDAPAY_CALLBACK_URL,
                    "timeout": 60,
                    "environment": settings.EASYSWITCH_ENVIRONMENT,
                    "extra": {
                        "webhook_secret": settings.EASYSWITCH_FEDAPAY_WEBHOOK_SECRET,
                    }
                }
            }
        }
        
        client = EasySwitch.from_dict(config)
        
        # if env_file:
        #     client = EasySwitch.from_env(env_file)
        
        client = client._get_integrator(Provider[str(settings.EASYSWITCH_DEFAULT_PROVIDER).upper()])

        return client
    
    def _validate_client_configuration(self) -> None:
        """Validate that the EasySwitch client is properly configured."""
        if not self._client:
            error = "Payment service not properly configured. EasySwitch client is not initialized."
            logger.error(error)
            raise ConfigurationError(
                detail=error
            )
        
        logger.info("Payment service initialized successfully")
    
    def create_transaction(self, transaction: T) -> T:
        """
        Create a new payment transaction with the provider.
        
        Args:
            transaction: Transaction instance to process
            
        Returns:
            Dictionary containing transaction details and status
            
        Raises:
            PaymentValidationError: If transaction data is invalid
            PaymentProcessingError: If payment processing fails
            ServiceUnavailableError: If payment service is unavailable
        """
        try:
            logger.info(f"Creating transaction {transaction.code} for user {transaction.user.id}")
            
            # Validate transaction before processing
            self._validate_transaction(transaction)
            
            # Prepare transaction data for provider
            transaction_detail = transaction.to_easyswitch_format()
            
            # Send payment request to provider
            response = self._send_payment_request(transaction_detail) 
                        
            # Process provider response
            result = self._process_payment_response(transaction, response)
            
            logger.info(f"Transaction {transaction.code} created successfully")
            
            return result
            
        except PaymentValidationError:
            logger.error(f"Transaction validation failed for {transaction.code}")
            transaction.fail()
            raise
        except PaymentProcessingError:
            logger.error(f"Payment processing failed for transaction {transaction.code}")
            transaction.fail()
            raise
        except Exception as e:
            error_message = f"Unexpected error creating transaction {transaction.code}: {str(e)}"
            logger.error(error_message)
            transaction.fail()
            
            raise PaymentProcessingError(
                detail=error_message
            )
    
    def _validate_transaction(self, transaction: T) -> None:
        """
        Validate transaction data before processing.
        
        Args:
            transaction: Transaction to validate
            
        Raises:
            PaymentValidationError: If validation fails
        """
        errors = []
                
        if not transaction.amount or transaction.amount <= 0:
            errors.append("Transaction amount must be greater than 0")
        
        if not transaction.currency:
            errors.append("Transaction currency is required")
        
        if not transaction.provider:
            errors.append("Payment provider is required")
        
        if not transaction.type:
            errors.append("Transaction type is required")
        
        if errors:
            raise PaymentValidationError(
                detail="Transaction validation failed; ".join(errors),
            )
    
    def _send_payment_request(self, transaction_detail: TransactionDetail) -> Any:
        """
        Send payment request to the provider.
        
        Args:
            transaction_detail: Transaction details for the provider
            
        Returns:
            Provider response
            
        Raises:
            PaymentProcessingError: If request fails
            ServiceUnavailableError: If service is unavailable
        """
          
        try:
            response = asyncio.run(self._client.send_payment(transaction_detail))

            if not response:
                error_message = f"No response received from payment provider"
                logger.error(error_message)
                
                raise PaymentProcessingError(error_message)
            
            return response
            
        except Exception as e:
            error_message = f"Failed to send payment request. Provider error: {str(e)}"
            logger.error(error_message)
            
            raise PaymentProcessingError(
                detail=error_message
            )
    
    def _process_payment_response(self, transaction: T, response: Any) -> T:
        """
        Process the payment provider response.
        
        Args:
            transaction: Transaction instance
            response: Provider response
            
        Returns:
            Processed response data
            
        Raises:
            PaymentProcessingError: If response processing fails
        """
        try:
            if not (hasattr(response, 'payment_link') and hasattr(response, 'status') and hasattr(response, 'reference')):
                logger.error(f"Invalid response from payment provider")
                raise PaymentProcessingError("Invalid response from payment provider")
            
            # Update transaction
            transaction.payment_link = response.payment_link
            transaction.reference = response.reference
            
            internal_status = self.map_easyswitch_status_to_internal(response.status)
            if internal_status:
                transaction.status = internal_status
            
            transaction.save()

            return transaction
            
        except Exception as e:
            logger.error(f"Failed to process payment response: {str(e)}")
            raise PaymentProcessingError(
                detail=f"Failed to process payment response. Response processing error: {str(e)}",
            )
    
    def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, Any]) -> WebhookEvent:
        """
        Process incoming webhook data from the payment provider.
                
        Args:
            payload: The data received from the payment provider webhook.
            headers: The headers received with the webhook request.

        Returns:
            WebhookEvent: The parsed webhook event from the payment provider.

        Raises:
            PaymentWebhookError: If the webhook parsing fails.
            TransactionNotFoundError: If the related transaction is not found.
            Exception: For any other unexpected errors.
        """
        try:
            # Parse webhook payload (async call)
            webhook_data: WebhookEvent = asyncio.run(
                self._client.parse_webhook(payload, headers)
            )
            logger.info(f"(process_webhook) Webhook data parsed: {webhook_data}")

            # Extract local transaction code safely
            metadata = webhook_data.metadata
            custom_metadata = metadata.get("custom_metadata", {})
            local_transaction_code = custom_metadata.get("Transaction", None)
            
            if not local_transaction_code:
                error = "Missing transaction description in webhook payload."
                logger.error(error)
                raise PaymentWebhookError(error)
        
            transaction = T.objects.get(code=local_transaction_code)
            
            if not transaction:
                error = f"Transaction not found: {str(e)}"
                logger.error(error)
                raise TransactionNotFoundError(error)
            
            self._call_process_webhook_functions(
                suffix=webhook_data.provider,
                webhook_data=webhook_data,
                transaction=transaction
            )

            # # Process according to provider
            # if transaction and webhook_data.provider == "fedapay":
            #     self._process_fedapay_webhook(webhook_data, transaction)

            return webhook_data
        
        except PaymentWebhookError as e:
            logger.error(f"Payment provider webhook error: {e}")
            raise
        except TransactionNotFoundError as e:
            logger.error(f"Transaction not found: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error while processing webhook: {e}")
            raise
    
    def _call_process_webhook_functions(self, suffix, **kwargs):
        """
        call the appropriate webhook process function
        Args:
            suffix (str): The provider name
        """
        function_name = '_process_' + suffix + '_webhook'

        # CHECK IF A FUNCTION "function_name" EXISTS AND IS CALLABLE
        if hasattr(self, function_name) and callable(getattr(self, function_name)):
            # THEN CALL IT WITH ARGUMENT
            getattr(self, function_name)(**kwargs)

        # RAISE EXCEPTION ELSE
        else:
            error = f'No member named _process_{suffix}_webhook or invalid webhook process type.'
            logger.error(error)
            raise PaymentWebhookError(error)

    def _process_fedapay_webhook(self, webhook_data: WebhookEvent, transaction: T) -> None:
        """
        Process Fedapay-specific webhook data.

        Args:
            webhook_data: The parsed webhook data.
            transaction: The transaction associated with the webhook.
        """        
        if webhook_data.status != transaction.status:
            transaction.status = self.get_internal_status_from_provider(webhook_data.status)
            transaction.save()

    # --- EASYSWITCH STATUS MAPPING ---
    
    def map_easyswitch_status_to_internal(self, provider_status: Union[str, EasySwitchTransactionStatus]) -> Optional[str]:
        """
        Map EasySwitch status to internal transaction status.
        
        Args:
            provider_status: Status from EasySwitch provider
            
        Returns:
            Internal status string or None if mapping not found
            
        Raises:
            PaymentValidationError: If status is invalid
        """
        status_mapping = {
            EasySwitchTransactionStatus.PENDING: T.STATUES.PENDING,
            EasySwitchTransactionStatus.SUCCESSFUL: T.STATUES.SUCCESSFUL,
            EasySwitchTransactionStatus.FAILED: T.STATUES.FAILED,
            EasySwitchTransactionStatus.ERROR: T.STATUES.FAILED,
            EasySwitchTransactionStatus.CANCELLED: T.STATUES.CANCELLED,
            EasySwitchTransactionStatus.REFUSED: T.STATUES.FAILED,
            EasySwitchTransactionStatus.DECLINED: T.STATUES.FAILED,
            EasySwitchTransactionStatus.EXPIRED: T.STATUES.FAILED,
            EasySwitchTransactionStatus.REFUNDED: T.STATUES.REFUNDED,
            EasySwitchTransactionStatus.PROCESSING: T.STATUES.PENDING,
            EasySwitchTransactionStatus.INITIATED: T.STATUES.PENDING,
            EasySwitchTransactionStatus.UNKNOWN: T.STATUES.FAILED,
            EasySwitchTransactionStatus.COMPLETED: T.STATUES.SUCCESSFUL,
            EasySwitchTransactionStatus.TRANSFERRED: T.STATUES.SUCCESSFUL,
        }
        
        # Handle string status values
        if isinstance(provider_status, str):
            try:
                provider_status = EasySwitchTransactionStatus[provider_status.upper()]
            except (KeyError, AttributeError):
                raise PaymentValidationError(
                    detail="Invalid provider status",
                    details=f"Unsupported status: {provider_status}"
                )
        
        return status_mapping.get(provider_status)
    
    def get_internal_status_from_provider(self, provider_status: str) -> str:
        """
        Get internal status from provider status string.
        
        Args:
            provider_status: Provider status string
            
        Returns:
            Internal status string
        """
        return self.map_easyswitch_status_to_internal(provider_status) or T.STATUES.FAILED
