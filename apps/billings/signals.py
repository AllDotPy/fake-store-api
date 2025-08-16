from django.db.models.signals import post_save
from django.dispatch import receiver
import logging
from asgiref.sync import sync_to_async, async_to_sync

from apps.accounts.models import User
from apps.billings.models import Transaction
from apps.billings.services import PaymentService

from apps.orders.models import Order
from core.exceptions import (
    PaymentInitiationError,
    PaymentProcessingError,
    PaymentValidationError
)

# Configure logger
logger = logging.getLogger(__name__)


####    CREATE TRANSACTION FOR ORDER
# @receiver(post_save, sender=Order)
# def create_transaction_for_order(sender, instance: Order, created, **kwargs):
#     ''' Create a Transaction for Order Payment. '''
    
#     print("(create_transaction_for_order) instance =", instance)
#     print("(create_transaction_for_order) instance =", instance.articles.all())
    
#     if created:
#         transaction = Transaction.objects.create(
#             user=instance.client,
#             order=instance,
#             type=Transaction.TYPES.PAYMENT,
#             # amount=float(instance.total()),
#             amount=100,
#         )
#         print("Created transaction:", transaction)
        
#         return transaction


## SEND TRANSACTION TO PROVIDER
@receiver(post_save, sender=Transaction)
def send_transaction_request(sender, instance: Transaction, created, **kwargs):
    ''' Send the newly created transaction to payment API and get checkout url. '''
    
    # OUR SIGNAL EVENT MUST BE A CREATE ACTION
    if created and instance.status == Transaction.STATUES.PENDING:
        # SEND TRANSACTION TO PROVIDER
        _ = PaymentService().create_transaction(
            transaction=instance
        )


## PROCESS ORDER PAYMENT SUCCESS
@receiver(post_save, sender=Transaction)
def process_order_payment_success(
    sender, instance: Transaction, 
    created, **kwargs
):
    ''' Process successful order payment. '''
    
    # CHECK IF TRANSACTION IS FOR ORDER AND SUCCESSFUL
    if (not created and 
        instance.type == Transaction.TYPES.PAYMENT and 
        instance.status == Transaction.STATUES.SUCCESSFUL and
        instance.order):
        
        try:
            logger.info(f"Processing successful payment for order {instance.order.code}")
            
            # UPDATE ORDER STATUS
            order = instance.order
            order.status = Order.OrderStatus.DELIVERING
            order.save()
            
            logger.info(f"Order {order.code} marked as paid successfully")
            
        except Exception as e:
            logger.error(f"Error processing order payment success: {str(e)}")
