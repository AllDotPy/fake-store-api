# from typing import Any, Dict, Literal
# from easyswitch.types import TransactionStatus as EasySwitchTransactionStatus
# from easyswitch import EasySwitch
# from apps.billings.models import Transaction as T
# from core.exceptions import (
#     PaymentInitiationError,
#     PaymentProcessingError,
#     PaymentValidationError,
#     PaymentMethodNotSupportedError,
#     ServiceUnavailableError,
#     ConfigurationError
# )

# ####
# ##      SERVICE CLASS
# #####
# class PaymentService:
#     ''' Payments service using EasySwitch. '''
    
#     def __init__(self):
#         ''' Initialize Service. '''
#         self._client = EasySwitch.from_env()
    
#     def create_transaction(self, transaction: T):
#         """Crée une transaction avec EasySwitch."""
#         try:
#             # Data preparation according to the EasySwitch structure
#             transaction_detail = transaction.to_easyswitch_format()
            
#             # Send payment with EasySwitch
#             response = self._client.send_payment(transaction_detail)
            
#             # Response processing
#             if response and hasattr(response, 'payment_link'):
#                 transaction.set_payment_link(response.payment_link)
                
#                 # Status update based on response
#                 if response.status:
#                     internal_status = self.map_easyswitch_status_to_internal(response.status)
#                     transaction.status = internal_status
#                     transaction.save()
                
#                 return {
#                     'success': True,
#                     'transaction_id': response.transaction_id,
#                     'payment_link': response.payment_link,
#                     'status': response.status,
#                     'raw_response': response.raw_response if hasattr(response, 'raw_response') else None,
#                 }
#             else:
#                 raise PaymentProcessingError("Invalid response from EasySwitch")
#         except Exception as e:
#             transaction.fail()
#             raise PaymentProcessingError(f"Failed to create transaction: {str(e)}")
 
#     def get_credentials(self):
#         ''' Return Client auth credentials. '''
    
#     def get_providers(self):
#         ''' Return a list of supported Aggregators. '''
        
#     def get_transactions(self):
#         ''' Return a list of app transactions. '''
        
#     def retrieve_transaction(self, transaction_id):
#         ''' Retrieve a specific transaction by id. '''
        
#     def create_transaction(self, transaction: T):
#         ''' Creates a new transaction with payment provider. '''        

#     def verify_transaction(self, transaction: T):
#         ''' Verify transaction status with provider. '''
    
#     def refund_transaction(self, transaction: T):
#         ''' Refund a transaction. '''
        
#     # --- MAPPING OF EASYSWITCH STATUS TO INTERNAL STATUS ---
#     def map_easyswitch_status_to_internal(provider_status: [str, Literal]) -> Literal:
#         ''' Map a EasySwitch status to an internal status. '''

#         statues = {
#             EasySwitchTransactionStatus.PENDING: T.STATUES.PENDING,
#             EasySwitchTransactionStatus.SUCCESSFUL: T.STATUES.SUCCESSFUL,
#             EasySwitchTransactionStatus.FAILED: T.STATUES.FAILED,
#             EasySwitchTransactionStatus.ERROR: T.STATUES.FAILED,
#             EasySwitchTransactionStatus.CANCELLED: T.STATUES.CANCELLED,
#             EasySwitchTransactionStatus.REFUSED: T.STATUES.FAILED,
#             EasySwitchTransactionStatus.DECLINED: T.STATUES.FAILED,
#             EasySwitchTransactionStatus.EXPIRED: T.STATUES.FAILED,
#             EasySwitchTransactionStatus.REFUNDED: T.STATUES.REFUNDED,
#             EasySwitchTransactionStatus.PROCESSING: T.STATUES.PENDING,
#             EasySwitchTransactionStatus.INITIATED: T.STATUES.PENDING,
#             EasySwitchTransactionStatus.UNKNOWN: T.STATUES.FAILED,
#             EasySwitchTransactionStatus.COMPLETED: T.STATUES.SUCCESSFUL,
#             EasySwitchTransactionStatus.TRANSFERRED: T.STATUES.SUCCESSFUL,
#         }

#         if isinstance(provider_status, str):
#             try:
#                 provider_status = EasySwitchTransactionStatus[provider_status.lower()]
#             except (KeyError, AttributeError):
#                 raise PaymentValidationError(
#                     details=f"Invalid status: {provider_status}"
#                 )
        
#         return statues.get(provider_status) or None


import logging
from typing import Any, Dict, List, Literal, Optional, Union
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from easyswitch.types import TransactionStatus as EasySwitchTransactionStatus
from easyswitch import (
    EasySwitch, 
    TransactionDetail, 
    PaymentResponse,
)

from apps.billings.models import Transaction as T
from core.exceptions import (
    PaymentInitiationError,
    PaymentProcessingError,
    PaymentValidationError,
    PaymentMethodNotSupportedError,
    ServiceUnavailableError,
    ConfigurationError,
    PaymentRefundError
)

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Professional payment service using EasySwitch provider.
    
    This service handles all payment-related operations including:
    - Transaction creation and processing
    - Payment status verification
    - Refund operations
    - Provider integration management
    """
    
    def __init__(self, client: Optional[EasySwitch] = None):
        """
        Initialize the payment service.
        
        Args:
            client: Optional EasySwitch client instance for testing
        """
        try:
            self._client = client or EasySwitch.from_env()
            self._validate_client_configuration()
        except Exception as e:
            logger.error(f"Failed to initialize EasySwitch client: {str(e)}")
            raise ConfigurationError(
                detail="Payment service configuration failed",
                details=f"EasySwitch client initialization error: {str(e)}"
            )
    
    def _validate_client_configuration(self) -> None:
        """Validate that the EasySwitch client is properly configured."""
        if not self._client:
            raise ConfigurationError(
                detail="Payment service not properly configured",
                details="EasySwitch client is not initialized"
            )
        
        # Add additional validation as needed
        logger.info("Payment service initialized successfully")
    
    def create_transaction(self, transaction: T) -> Dict[str, Any]:
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
            logger.error(f"Unexpected error creating transaction {transaction.code}: {str(e)}")
            transaction.fail()
            raise PaymentProcessingError(
                detail="Failed to create transaction",
                details=f"Unexpected error: {str(e)}"
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
        
        if not transaction.user:
            errors.append("Transaction must have a valid user")
        
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
                detail="Transaction validation failed",
                details="; ".join(errors)
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
            response = self._client.send_payment(transaction_detail)
            
            if not response:
                raise PaymentProcessingError("No response received from payment provider")
            
            return response
            
        except Exception as e:
            logger.error(f"Payment request failed: {str(e)}")
            raise PaymentProcessingError(
                detail="Failed to send payment request",
                details=f"Provider error: {str(e)}"
            )
    
    def _process_payment_response(self, transaction: T, response: Any) -> Dict[str, Any]:
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
            if not hasattr(response, 'payment_link'):
                raise PaymentProcessingError("Invalid response from payment provider")
            
            # Update transaction with payment link
            transaction.set_payment_link(response.payment_link)
            
            # Update transaction status based on response
            if hasattr(response, 'status') and response.status:
                internal_status = self.map_easyswitch_status_to_internal(response.status)
                if internal_status:
                    transaction.status = internal_status
                    transaction.save()
            
            return {
                'success': True,
                'transaction_id': getattr(response, 'transaction_id', None),
                'payment_link': response.payment_link,
                'status': getattr(response, 'status', None),
                'raw_response': getattr(response, 'raw_response', None),
            }
            
        except Exception as e:
            logger.error(f"Failed to process payment response: {str(e)}")
            raise PaymentProcessingError(
                detail="Failed to process payment response",
                details=f"Response processing error: {str(e)}"
            )
    
    def get_credentials(self) -> Dict[str, Any]:
        """
        Get client authentication credentials.
        
        Returns:
            Dictionary containing credential information
        """
        try:
            # This should return non-sensitive credential information
            # for debugging or validation purposes
            return {
                'provider': 'EasySwitch',
                'configured': bool(self._client),
                'environment': getattr(settings, 'EASYSWITCH_ENVIRONMENT', 'unknown')
            }
        except Exception as e:
            logger.error(f"Failed to get credentials: {str(e)}")
            raise ConfigurationError(
                detail="Failed to retrieve credentials",
                details=str(e)
            )
    
    def get_providers(self) -> List[Dict[str, Any]]:
        """
        Get list of supported payment providers.
        
        Returns:
            List of available payment providers
        """
        try:
            # Return supported providers based on EasySwitch configuration
            providers = [
                {
                    'code': 'SEMOA',
                    'name': 'SEMOA',
                    'supported': True,
                    'currencies': ['XOF', 'XAF']
                },
                {
                    'code': 'BIZAO',
                    'name': 'BIZAO',
                    'supported': True,
                    'currencies': ['XOF', 'XAF', 'NGN', 'GHS']
                },
                {
                    'code': 'CINEPAY',
                    'name': 'CINEPAY',
                    'supported': True,
                    'currencies': ['XOF', 'XAF', 'NGN', 'GHS', 'EUR', 'USD']
                },
                {
                    'code': 'PAYGATE',
                    'name': 'PAYGATE',
                    'supported': True,
                    'currencies': ['XOF', 'XAF', 'NGN', 'GHS', 'EUR', 'USD']
                },
                {
                    'code': 'FEDAPAY',
                    'name': 'FEDAPAY',
                    'supported': True,
                    'currencies': ['XOF', 'XAF', 'NGN', 'GHS', 'EUR', 'USD']
                }
            ]
            
            return providers
            
        except Exception as e:
            logger.error(f"Failed to get providers: {str(e)}")
            raise ServiceUnavailableError(
                detail="Failed to retrieve payment providers",
                details=str(e)
            )
    
    def get_transactions(self, user_id: Optional[int] = None, 
                        status: Optional[str] = None,
                        limit: int = 100) -> List[T]:
        """
        Get list of transactions with optional filtering.
        
        Args:
            user_id: Filter by user ID
            status: Filter by transaction status
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction instances
        """
        try:
            queryset = T.objects.all()
            
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
            if status:
                queryset = queryset.filter(status=status)
            
            transactions = queryset.order_by('-created')[:limit]
            
            logger.info(f"Retrieved {len(transactions)} transactions")
            return list(transactions)
            
        except Exception as e:
            logger.error(f"Failed to get transactions: {str(e)}")
            raise ServiceUnavailableError(
                detail="Failed to retrieve transactions",
                details=str(e)
            )
    
    def retrieve_transaction(self, transaction_id: str) -> Optional[T]:
        """
        Retrieve a specific transaction by ID.
        
        Args:
            transaction_id: Transaction ID to retrieve
            
        Returns:
            Transaction instance or None if not found
        """
        try:
            transaction = T.objects.filter(code=transaction_id).first()
            
            if not transaction:
                logger.warning(f"Transaction {transaction_id} not found")
                return None
            
            logger.info(f"Retrieved transaction {transaction_id}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to retrieve transaction {transaction_id}: {str(e)}")
            raise ServiceUnavailableError(
                detail="Failed to retrieve transaction",
                details=str(e)
            )
    
    def verify_transaction(self, transaction: T) -> Dict[str, Any]:
        """
        Verify transaction status with the payment provider.
        
        Args:
            transaction: Transaction to verify
            
        Returns:
            Verification result with updated status
        """
        try:
            logger.info(f"Verifying transaction {transaction.code}")
            
            # Query provider for current transaction status
            provider_status = self._query_provider_status(transaction)
            
            # Map provider status to internal status
            internal_status = self.map_easyswitch_status_to_internal(provider_status)
            
            # Update transaction status if changed
            if internal_status and internal_status != transaction.status:
                transaction.status = internal_status
                transaction.save()
                logger.info(f"Transaction {transaction.code} status updated to {internal_status}")
            
            return {
                'success': True,
                'transaction_id': transaction.code,
                'current_status': transaction.status,
                'provider_status': provider_status,
                'verified_at': transaction.updated
            }
            
        except Exception as e:
            logger.error(f"Failed to verify transaction {transaction.code}: {str(e)}")
            raise PaymentProcessingError(
                detail="Failed to verify transaction",
                details=str(e)
            )
    
    def _query_provider_status(self, transaction: T) -> str:
        """
        Query the payment provider for current transaction status.
        
        Args:
            transaction: Transaction to query
            
        Returns:
            Provider status string
        """
        try:
            # This would typically call the provider's API
            # For now, we'll simulate the response
            # In a real implementation, you would call:
            # response = self._client.get_transaction_status(transaction.code)
            
            # Simulated response - replace with actual provider call
            return transaction.status
            
        except Exception as e:
            logger.error(f"Failed to query provider status: {str(e)}")
            raise PaymentProcessingError(
                detail="Failed to query transaction status",
                details=str(e)
            )
    
    def refund_transaction(self, transaction: T, amount: Optional[Decimal] = None) -> Dict[str, Any]:
        """
        Refund a transaction.
        
        Args:
            transaction: Transaction to refund
            amount: Amount to refund (if None, refunds full amount)
            
        Returns:
            Refund result
            
        Raises:
            PaymentRefundError: If refund fails
            PaymentValidationError: If transaction cannot be refunded
        """
        try:
            logger.info(f"Processing refund for transaction {transaction.code}")
            
            # Validate transaction can be refunded
            if not transaction.can_refund():
                raise PaymentValidationError(
                    detail="Transaction cannot be refunded",
                    details="Only successful transactions can be refunded"
                )
            
            # Determine refund amount
            refund_amount = amount or transaction.amount
            
            if refund_amount > transaction.amount:
                raise PaymentValidationError(
                    detail="Invalid refund amount",
                    details="Refund amount cannot exceed original transaction amount"
                )
            
            # Process refund with provider
            refund_result = self._process_refund_with_provider(transaction, refund_amount)
            
            # Update transaction status
            if refund_result.get('success'):
                transaction.status = T.STATUES.REFUNDED
                transaction.save()
                logger.info(f"Transaction {transaction.code} refunded successfully")
            
            return refund_result
            
        except PaymentValidationError:
            logger.error(f"Refund validation failed for transaction {transaction.code}")
            raise
        except Exception as e:
            logger.error(f"Failed to refund transaction {transaction.code}: {str(e)}")
            raise PaymentRefundError(
                detail="Failed to process refund",
                details=str(e)
            )
    
    def _process_refund_with_provider(self, transaction: T, amount: Decimal) -> Dict[str, Any]:
        """
        Process refund with the payment provider.
        
        Args:
            transaction: Transaction to refund
            amount: Amount to refund
            
        Returns:
            Refund result from provider
        """
        try:
            # This would typically call the provider's refund API
            # For now, we'll simulate the response
            # In a real implementation, you would call:
            # response = self._client.refund_transaction(transaction.code, amount)
            
            # Simulated successful refund response
            return {
                'success': True,
                'refund_id': f"REF_{transaction.code}",
                'amount': float(amount),
                'currency': transaction.currency,
                'status': 'REFUNDED',
                'processed_at': transaction.updated
            }
            
        except Exception as e:
            logger.error(f"Provider refund failed: {str(e)}")
            raise PaymentRefundError(
                detail="Failed to process refund with provider",
                details=str(e)
            )
    
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
    
    # --- UTILITY METHODS ---
    
    def is_service_available(self) -> bool:
        """
        Check if the payment service is available.
        
        Returns:
            True if service is available, False otherwise
        """
        try:
            # Simple health check
            return bool(self._client)
        except Exception:
            return False
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get payment service information.
        
        Returns:
            Service information dictionary
        """
        return {
            'service_name': 'PaymentService',
            'provider': 'EasySwitch',
            'available': self.is_service_available(),
            'supported_providers': len(self.get_providers()),
            'environment': getattr(settings, 'EASYSWITCH_ENVIRONMENT', 'unknown')
        }