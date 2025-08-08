"""
Tests for PaymentService.

This module contains comprehensive tests for the PaymentService class,
including unit tests, integration tests, and edge case handling.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings

from apps.billings.models import Transaction
from apps.billings.services import PaymentService
from core.exceptions import (
    PaymentInitiationError,
    PaymentProcessingError,
    PaymentValidationError,
    PaymentRefundError,
    ConfigurationError
)

User = get_user_model()


class PaymentServiceTestCase(TestCase):
    """Base test case for PaymentService tests."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone_number='+1234567890'
        )
        
        self.transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            currency='XOF',
            provider='SEMOA',
            type='PAYMENT',
            description='Test payment'
        )
        
        # Mock EasySwitch client
        self.mock_client = Mock()
        self.payment_service = PaymentService(client=self.mock_client)


class PaymentServiceInitializationTests(PaymentServiceTestCase):
    """Test PaymentService initialization."""
    
    def test_initialization_with_client(self):
        """Test initialization with provided client."""
        service = PaymentService(client=self.mock_client)
        self.assertIsNotNone(service)
        self.assertEqual(service._client, self.mock_client)
    
    @patch('apps.billings.services.EasySwitch.from_env')
    def test_initialization_without_client(self, mock_from_env):
        """Test initialization without client (uses EasySwitch.from_env)."""
        mock_from_env.return_value = self.mock_client
        service = PaymentService()
        self.assertIsNotNone(service)
        mock_from_env.assert_called_once()
    
    @patch('apps.billings.services.EasySwitch.from_env')
    def test_initialization_failure(self, mock_from_env):
        """Test initialization failure raises ConfigurationError."""
        mock_from_env.side_effect = Exception("Configuration error")
        
        with self.assertRaises(ConfigurationError):
            PaymentService()


class PaymentServiceValidationTests(PaymentServiceTestCase):
    """Test transaction validation methods."""
    
    def test_validate_transaction_success(self):
        """Test successful transaction validation."""
        # Should not raise any exception
        self.payment_service._validate_transaction(self.transaction)
    
    def test_validate_transaction_no_user(self):
        """Test validation failure when transaction has no user."""
        self.transaction.user = None
        
        with self.assertRaises(PaymentValidationError) as cm:
            self.payment_service._validate_transaction(self.transaction)
        
        self.assertIn("valid user", str(cm.exception))
    
    def test_validate_transaction_invalid_amount(self):
        """Test validation failure with invalid amount."""
        self.transaction.amount = Decimal('0.00')
        
        with self.assertRaises(PaymentValidationError) as cm:
            self.payment_service._validate_transaction(self.transaction)
        
        self.assertIn("greater than 0", str(cm.exception))
    
    def test_validate_transaction_no_currency(self):
        """Test validation failure when currency is missing."""
        self.transaction.currency = ''
        
        with self.assertRaises(PaymentValidationError) as cm:
            self.payment_service._validate_transaction(self.transaction)
        
        self.assertIn("currency is required", str(cm.exception))
    
    def test_validate_transaction_no_provider(self):
        """Test validation failure when provider is missing."""
        self.transaction.provider = ''
        
        with self.assertRaises(PaymentValidationError) as cm:
            self.payment_service._validate_transaction(self.transaction)
        
        self.assertIn("provider is required", str(cm.exception))
    
    def test_validate_transaction_no_type(self):
        """Test validation failure when type is missing."""
        self.transaction.type = ''
        
        with self.assertRaises(PaymentValidationError) as cm:
            self.payment_service._validate_transaction(self.transaction)
        
        self.assertIn("type is required", str(cm.exception))


class PaymentServiceCreateTransactionTests(PaymentServiceTestCase):
    """Test transaction creation methods."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.mock_response = Mock()
        self.mock_response.payment_link = 'https://payment.example.com/pay'
        self.mock_response.transaction_id = 'TXN_123'
        self.mock_response.status = 'PENDING'
    
    @patch.object(Transaction, 'to_easyswitch_format')
    def test_create_transaction_success(self, mock_to_format):
        """Test successful transaction creation."""
        # Mock transaction format
        mock_transaction_detail = Mock()
        mock_to_format.return_value = mock_transaction_detail
        
        # Mock client response
        self.mock_client.send_payment.return_value = self.mock_response
        
        # Mock status mapping
        with patch.object(self.payment_service, 'map_easyswitch_status_to_internal') as mock_map:
            mock_map.return_value = Transaction.STATUES.PENDING
            
            result = self.payment_service.create_transaction(self.transaction)
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertEqual(result['transaction_id'], 'TXN_123')
        self.assertEqual(result['payment_link'], 'https://payment.example.com/pay')
        
        # Verify transaction was updated
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.payment_link, 'https://payment.example.com/pay')
    
    def test_create_transaction_validation_failure(self):
        """Test transaction creation with validation failure."""
        self.transaction.amount = Decimal('0.00')
        
        with self.assertRaises(PaymentValidationError):
            self.payment_service.create_transaction(self.transaction)
        
        # Verify transaction was marked as failed
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, Transaction.STATUES.FAILED)
    
    def test_create_transaction_provider_failure(self):
        """Test transaction creation when provider fails."""
        self.mock_client.send_payment.side_effect = Exception("Provider error")
        
        with self.assertRaises(PaymentProcessingError):
            self.payment_service.create_transaction(self.transaction)
        
        # Verify transaction was marked as failed
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, Transaction.STATUES.FAILED)
    
    def test_create_transaction_invalid_response(self):
        """Test transaction creation with invalid provider response."""
        invalid_response = Mock()
        invalid_response.payment_link = None  # Missing required attribute
        
        self.mock_client.send_payment.return_value = invalid_response
        
        with self.assertRaises(PaymentProcessingError):
            self.payment_service.create_transaction(self.transaction)


class PaymentServiceStatusMappingTests(PaymentServiceTestCase):
    """Test status mapping functionality."""
    
    def test_map_easyswitch_status_to_internal_success(self):
        """Test successful status mapping."""
        from easyswitch.types import TransactionStatus as EasySwitchTransactionStatus
        
        # Test various status mappings
        test_cases = [
            (EasySwitchTransactionStatus.PENDING, Transaction.STATUES.PENDING),
            (EasySwitchTransactionStatus.SUCCESSFUL, Transaction.STATUES.SUCCESSFUL),
            (EasySwitchTransactionStatus.FAILED, Transaction.STATUES.FAILED),
            (EasySwitchTransactionStatus.CANCELLED, Transaction.STATUES.CANCELLED),
            (EasySwitchTransactionStatus.REFUNDED, Transaction.STATUES.REFUNDED),
        ]
        
        for provider_status, expected_internal_status in test_cases:
            result = self.payment_service.map_easyswitch_status_to_internal(provider_status)
            self.assertEqual(result, expected_internal_status)
    
    def test_map_easyswitch_status_to_internal_string(self):
        """Test status mapping with string input."""
        result = self.payment_service.map_easyswitch_status_to_internal('PENDING')
        self.assertEqual(result, Transaction.STATUES.PENDING)
    
    def test_map_easyswitch_status_to_internal_invalid_string(self):
        """Test status mapping with invalid string input."""
        with self.assertRaises(PaymentValidationError):
            self.payment_service.map_easyswitch_status_to_internal('INVALID_STATUS')
    
    def test_map_easyswitch_status_to_internal_unknown_status(self):
        """Test status mapping with unknown status."""
        from easyswitch.types import TransactionStatus as EasySwitchTransactionStatus
        
        # Test with a status that's not in our mapping
        unknown_status = EasySwitchTransactionStatus.UNKNOWN
        result = self.payment_service.map_easyswitch_status_to_internal(unknown_status)
        self.assertEqual(result, Transaction.STATUES.FAILED)
    
    def test_get_internal_status_from_provider(self):
        """Test getting internal status from provider status."""
        result = self.payment_service.get_internal_status_from_provider('SUCCESSFUL')
        self.assertEqual(result, Transaction.STATUES.SUCCESSFUL)
        
        # Test with invalid status (should return FAILED)
        result = self.payment_service.get_internal_status_from_provider('INVALID')
        self.assertEqual(result, Transaction.STATUES.FAILED)


class PaymentServiceRefundTests(PaymentServiceTestCase):
    """Test refund functionality."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Make transaction successful for refund tests
        self.transaction.status = Transaction.STATUES.SUCCESSFUL
        self.transaction.save()
    
    def test_refund_transaction_success(self):
        """Test successful transaction refund."""
        with patch.object(self.payment_service, '_process_refund_with_provider') as mock_refund:
            mock_refund.return_value = {'success': True, 'refund_id': 'REF_123'}
            
            result = self.payment_service.refund_transaction(self.transaction)
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertEqual(result['refund_id'], 'REF_123')
        
        # Verify transaction status was updated
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.status, Transaction.STATUES.REFUNDED)
    
    def test_refund_transaction_partial_amount(self):
        """Test partial refund."""
        refund_amount = Decimal('50.00')
        
        with patch.object(self.payment_service, '_process_refund_with_provider') as mock_refund:
            mock_refund.return_value = {'success': True, 'refund_id': 'REF_123'}
            
            result = self.payment_service.refund_transaction(self.transaction, refund_amount)
        
        # Verify refund was called with correct amount
        mock_refund.assert_called_once_with(self.transaction, refund_amount)
    
    def test_refund_transaction_cannot_refund(self):
        """Test refund when transaction cannot be refunded."""
        self.transaction.status = Transaction.STATUES.PENDING
        self.transaction.save()
        
        with self.assertRaises(PaymentValidationError) as cm:
            self.payment_service.refund_transaction(self.transaction)
        
        self.assertIn("cannot be refunded", str(cm.exception))
    
    def test_refund_transaction_invalid_amount(self):
        """Test refund with invalid amount."""
        invalid_amount = Decimal('200.00')  # More than original amount
        
        with self.assertRaises(PaymentValidationError) as cm:
            self.payment_service.refund_transaction(self.transaction, invalid_amount)
        
        self.assertIn("cannot exceed", str(cm.exception))
    
    def test_refund_transaction_provider_failure(self):
        """Test refund when provider fails."""
        with patch.object(self.payment_service, '_process_refund_with_provider') as mock_refund:
            mock_refund.side_effect = Exception("Provider error")
            
            with self.assertRaises(PaymentRefundError):
                self.payment_service.refund_transaction(self.transaction)


class PaymentServiceUtilityTests(PaymentServiceTestCase):
    """Test utility methods."""
    
    def test_get_credentials(self):
        """Test getting credentials."""
        result = self.payment_service.get_credentials()
        
        self.assertIn('provider', result)
        self.assertIn('configured', result)
        self.assertEqual(result['provider'], 'EasySwitch')
        self.assertTrue(result['configured'])
    
    def test_get_providers(self):
        """Test getting supported providers."""
        providers = self.payment_service.get_providers()
        
        self.assertIsInstance(providers, list)
        self.assertGreater(len(providers), 0)
        
        # Check that each provider has required fields
        for provider in providers:
            self.assertIn('code', provider)
            self.assertIn('name', provider)
            self.assertIn('supported', provider)
            self.assertIn('currencies', provider)
    
    def test_get_transactions(self):
        """Test getting transactions."""
        # Create additional transactions
        Transaction.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            currency='XOF',
            provider='BIZAO',
            type='PAYMENT'
        )
        
        transactions = self.payment_service.get_transactions()
        self.assertEqual(len(transactions), 2)
        
        # Test filtering by user
        transactions = self.payment_service.get_transactions(user_id=self.user.id)
        self.assertEqual(len(transactions), 2)
        
        # Test filtering by status
        transactions = self.payment_service.get_transactions(status=Transaction.STATUES.PENDING)
        self.assertEqual(len(transactions), 2)
    
    def test_retrieve_transaction(self):
        """Test retrieving specific transaction."""
        transaction = self.payment_service.retrieve_transaction(self.transaction.code)
        self.assertEqual(transaction, self.transaction)
        
        # Test with non-existent transaction
        result = self.payment_service.retrieve_transaction('NON_EXISTENT')
        self.assertIsNone(result)
    
    def test_verify_transaction(self):
        """Test transaction verification."""
        with patch.object(self.payment_service, '_query_provider_status') as mock_query:
            mock_query.return_value = 'SUCCESSFUL'
            
            result = self.payment_service.verify_transaction(self.transaction)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['transaction_id'], self.transaction.code)
    
    def test_is_service_available(self):
        """Test service availability check."""
        self.assertTrue(self.payment_service.is_service_available())
        
        # Test with no client
        service = PaymentService(client=None)
        self.assertFalse(service.is_service_available())
    
    def test_get_service_info(self):
        """Test getting service information."""
        info = self.payment_service.get_service_info()
        
        self.assertIn('service_name', info)
        self.assertIn('provider', info)
        self.assertIn('available', info)
        self.assertIn('supported_providers', info)
        self.assertIn('environment', info)
        
        self.assertEqual(info['service_name'], 'PaymentService')
        self.assertEqual(info['provider'], 'EasySwitch')


class PaymentServiceIntegrationTests(PaymentServiceTestCase):
    """Integration tests for PaymentService."""
    
    def test_full_payment_flow(self):
        """Test complete payment flow from creation to verification."""
        # Mock the entire flow
        with patch.object(Transaction, 'to_easyswitch_format') as mock_format:
            mock_transaction_detail = Mock()
            mock_format.return_value = mock_transaction_detail
            
            # Mock successful payment response
            mock_response = Mock()
            mock_response.payment_link = 'https://payment.example.com/pay'
            mock_response.transaction_id = 'TXN_123'
            mock_response.status = 'PENDING'
            
            self.mock_client.send_payment.return_value = mock_response
            
            # Create transaction
            result = self.payment_service.create_transaction(self.transaction)
            self.assertTrue(result['success'])
            
            # Verify transaction
            with patch.object(self.payment_service, '_query_provider_status') as mock_query:
                mock_query.return_value = 'SUCCESSFUL'
                
                verify_result = self.payment_service.verify_transaction(self.transaction)
                self.assertTrue(verify_result['success'])
    
    def test_error_handling_flow(self):
        """Test error handling throughout the payment flow."""
        # Test validation error
        self.transaction.amount = Decimal('0.00')
        
        with self.assertRaises(PaymentValidationError):
            self.payment_service.create_transaction(self.transaction)
        
        # Reset transaction
        self.transaction.amount = Decimal('100.00')
        self.transaction.status = Transaction.STATUES.PENDING
        self.transaction.save()
        
        # Test provider error
        self.mock_client.send_payment.side_effect = Exception("Provider unavailable")
        
        with self.assertRaises(PaymentProcessingError):
            self.payment_service.create_transaction(self.transaction)


# Performance tests
class PaymentServicePerformanceTests(PaymentServiceTestCase):
    """Performance tests for PaymentService."""
    
    def test_bulk_transaction_creation(self):
        """Test creating multiple transactions efficiently."""
        transactions = []
        for i in range(10):
            transaction = Transaction.objects.create(
                user=self.user,
                amount=Decimal(f'{10 + i}.00'),
                currency='XOF',
                provider='SEMOA',
                type='PAYMENT'
            )
            transactions.append(transaction)
        
        # Mock provider responses
        mock_response = Mock()
        mock_response.payment_link = 'https://payment.example.com/pay'
        mock_response.transaction_id = 'TXN_123'
        mock_response.status = 'PENDING'
        
        self.mock_client.send_payment.return_value = mock_response
        
        # Process all transactions
        results = []
        for transaction in transactions:
            with patch.object(Transaction, 'to_easyswitch_format'):
                result = self.payment_service.create_transaction(transaction)
                results.append(result)
        
        # Verify all transactions were processed
        self.assertEqual(len(results), 10)
        for result in results:
            self.assertTrue(result['success'])


# Edge case tests
class PaymentServiceEdgeCaseTests(PaymentServiceTestCase):
    """Edge case tests for PaymentService."""
    
    def test_transaction_with_minimal_data(self):
        """Test transaction with minimal required data."""
        minimal_transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('1.00'),
            currency='XOF',
            provider='SEMOA',
            type='PAYMENT'
        )
        
        # Should not raise any validation errors
        self.payment_service._validate_transaction(minimal_transaction)
    
    def test_transaction_with_maximum_data(self):
        """Test transaction with all possible data."""
        self.transaction.description = "Very long description " * 100
        self.transaction.payment_method = "MOBILE_MONEY"
        
        # Should not raise any validation errors
        self.payment_service._validate_transaction(self.transaction)
    
    def test_unicode_handling(self):
        """Test handling of unicode characters in transaction data."""
        self.transaction.description = "Paiement avec caractères spéciaux: éàçù"
        
        # Should not raise any validation errors
        self.payment_service._validate_transaction(self.transaction)
    
    def test_large_amount_handling(self):
        """Test handling of large transaction amounts."""
        self.transaction.amount = Decimal('999999.99')
        
        # Should not raise any validation errors
        self.payment_service._validate_transaction(self.transaction) 