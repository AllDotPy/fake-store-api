from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

from apps.accounts.models import User, Student
from apps.billings.models import Transaction
from apps.billings.services import PaymentService

from core.exceptions import (
    PaymentInitiationError,
    PaymentProcessingError,
    PaymentValidationError
)

# Configure logger
logger = logging.getLogger(__name__)


####    CREATE TRANSACTION FOR ORDER
def create_transaction_for_order(order, amount, payment_method=None):
    ''' Create a Transaction for Order Payment. '''

    transaction = Transaction.objects.create(
        user=order.user,
        order=order,
        subject=Transaction.SUBJECTS.ORDER_PAYMENT,
        amount=amount,
        payment_method=payment_method,
        description=f"Payment for order {order.code}"
    )
    return transaction


## SEND TRANSACTION TO PROVIDER
@receiver(post_save, sender=Transaction, weak=False)
def send_transaction_request(sender, instance: Transaction, created, **kwargs):
    ''' Send the newly created transaction to payment API and get checkout url. '''
    
    # OUR SIGNAL EVENT MUST BE A CREATE ACTION
    if created and instance.status == Transaction.STATUES.PENDING:
        try:
            logger.info(f"Processing transaction {instance.code} for user {instance.user.id}")
            
            # SEND TRANSACTION TO PROVIDER
            response = PaymentService().create_transaction(
                transaction=instance
            )
            
            # CHECK FOR SUCCESS
            if not response.has_error and response.json:
                logger.info(f"Transaction {instance.code} created successfully with provider")
                
                # UPDATE TRANSACTION STATUS IF NEEDED
                if response.json.get('status') == 'SUCCESS':
                    instance.succeed()
                    
            else:
                logger.error(f"Transaction creation failed: {response.get_message()}")
                instance.fail()
                
        except PaymentValidationError as e:
            logger.error(f"Payment validation error for transaction {instance.code}: {str(e)}")
            instance.fail()
            
        except PaymentInitiationError as e:
            logger.error(f"Payment initiation error for transaction {instance.code}: {str(e)}")
            instance.fail()
            
        except PaymentProcessingError as e:
            logger.error(f"Payment processing error for transaction {instance.code}: {str(e)}")
            instance.fail()
            
        except Exception as e:
            logger.error(f"Unexpected error processing transaction {instance.code}: {str(e)}")
            instance.fail()


## PROCESS ORDER PAYMENT SUCCESS
@receiver(post_save, sender=Transaction, weak=False)
def process_order_payment_success(
    sender, instance: Transaction, 
    created, **kwargs
):
    ''' Process successful order payment. '''
    
    # CHECK IF TRANSACTION IS FOR ORDER AND SUCCESSFUL
    if (not created and 
        instance.subject == Transaction.SUBJECTS.ORDER_PAYMENT and 
        instance.status == Transaction.STATUES.SUCCESS and
        instance.order):
        
        try:
            logger.info(f"Processing successful payment for order {instance.order.code}")
            
            # UPDATE ORDER STATUS
            order = instance.order
            order.status = 'PAID'  # Assuming Order model has status field
            order.save()
            
            logger.info(f"Order {order.code} marked as paid successfully")
            
        except Exception as e:
            logger.error(f"Error processing order payment success: {str(e)}")


## PROCESS SUBSCRIPTION TRANSACTION
@receiver(post_save, sender=Transaction, weak=False)
def process_subscription_transaction(
    sender, instance: Transaction, 
    created, **kwargs
):
    ''' Process subscription transaction. '''
    
    # OUR SIGNAL EVENT MUST BE A CREATE ACTION
    if created and instance.subject == Transaction.SUBJECTS.SUBSCRIPTION:
        try:
            logger.info(f"Processing subscription transaction {instance.code}")
            
            # TODO: Implement subscription processing logic
            logger.info(f"Subscription transaction {instance.code} processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing subscription: {str(e)}")
            instance.fail()
