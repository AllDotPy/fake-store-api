from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import (
    User, Student
)
from apps.billings.models import (
    Transaction, Wallet,
    RechargeTransaction,
    StudentRentTransaction,
    CollectionTransaction
)

from apps.billings.services import (
    PaymentService
)

from apps.utils.functions import (
    get_free_trial_balance,
    get_students_exam_test_price,
    get_students_exercice_price
    # create_notification,send_notification
)
# from apps.billings import services

####    CREATE TRANSACTION FOR COLLECTION
def create_transaction_for_collection(collection,amount,exo = True):
    ''' Create a Transaction for Student Rent. '''

    d = {
        'exo': collection if exo else None,
        'exam': collection if not exo else None
    }

    # CREATE TRANSACTION OBJECT
    transaction = CollectionTransaction.objects.create(
        **d,
        amount = amount,
        status = CollectionTransaction.STATUES.PENDING
    )
    return transaction


## CREAYE WALLET FOR EVERY NEWLY CREADTED USER
@receiver(post_save, sender = Student, weak = False)
def create_wallet_for_user(sender, instance:User, created, **kwargs):
    """
    This function will be called after new user registration.
    It creates automatically a Wallet for newly created user object .
    """

    # OUR SIGNAL EVENT MUST BE A CREATE ACTION
    if created:
        # CREATE WALLET OBJECT
        wallet = Wallet.objects.create(
            user = instance, balance = get_free_trial_balance()
        )
        
        
## SEND TRANSACTION TO PROVIDER
@receiver(post_save, sender=RechargeTransaction, weak = False)
def send_transaction_request(sender, instance:RechargeTransaction, created, **kwargs):
    ''' Send the newly created transaction to payment API and get checkout url. '''
    
    # OUR SIGNAL EVENT MUST BE A CREATE ACTION
    if created:
        # SEND TRANSACTION TO PROVIDER
        res = PaymentService().crate_transaction(
            transaction = instance
        )
        
        # CHECK FOR SUCCESS
        if not res.has_error:
            # THEN SET INSTANCE BILL URL
            instance.set_bill_url(
                res.json.get('bill_url')
            )
            print(res.json)
        else: print(res.get_message)


## PROCESS SUBSCRIPTION TRANSACTION
@receiver(post_save, sender=StudentRentTransaction, weak = False)
def process_subscription_transaction(
    sender, instance:StudentRentTransaction, 
    created, **kwargs
):
    ''' Process the newly created transaction. '''
    
    # OUR SIGNAL EVENT MUST BE A CREATE ACTION
    if created:
        # THEN PROCEED THE TRANSACTION
        instance.proceed()
