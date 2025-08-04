from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.utils.models import TimeStampedUUIDModel
from apps.accounts.models import (
    User
)

from apps.utils.functions import(
    get_object_or_None, get_host_url
)
# import apps.billings.services

# Create your models here.


####
##      WALLET MODEL
#####
class Wallet(TimeStampedUUIDModel):
    ''' Store Informations about user wallet. '''

    balance = models.IntegerField(
        default = 0,
    )
    user = models.OneToOneField(
        User, on_delete = models.CASCADE,
        related_name = 'wallet'
    )

    # META CLASS
    class Meta:
        ''' Meta class for Wallet Model. '''

        verbose_name = _("Wallet")
        verbose_name_plural = _("Wallets")
        ordering = ['-created']

    def __str__(self):
        return f'{self.user} - {self.balance}'

    def get_id_prefix(self):
        return 'WALL'

    def credit(self,amount):
        ''' Credit a user wallet for a given amount. '''

        self.balance += amount
        self.save()

    def debit(self,amount):
        ''' Debit a user wallet for a given amount. '''

        self.balance -= amount
        self.save()

    def can_process(self,amount):
        ''' 
            return True if wallet balance has enougth 
            money to process amount transaction else False. 
        '''
        return self.balance > amount

    def is_empty(self):
        ''' Check that wallet balance is empty. '''

        return self.balance == 0
        
        
####
##       BASE TRANSACTION MODEL
#####
class Transaction(TimeStampedUUIDModel):
    ''' Store informations about Transactions. '''

    # SUBJECTS CHOICES
    class SUBJECTS(models.TextChoices):
        ''' Transaction object types. '''

        RENT = 'SUBSCRIPTION',_('SUBSCRIPTION')
        # REFUND = 'REFUND',_('REFUND')
        RECHARGE = 'RECHARGE',_('RECHARGE')
        COLLECTION = 'COLLECTION',_('COLLECTION')

    # TYPES CHOICES
    class TYPES(models.TextChoices):
        ''' Transaction types. '''

        DEBIT = 'DEBIT',_('DEBIT')
        CREDIT = 'CREDIT',_('CREDIT')

    # STATUES CHOICES
    class STATUES(models.TextChoices):
        ''' Transaction statues. '''

        PENDING = 'PENDING',_('PENDING')
        SUCCESS = 'SUCCESS',_('SUCCESS')
        FAILURE = 'FAILURE',_('FAILURE')
        REFOUNDED = 'REFOUNDED',_('REFOUNDED')

    subject = models.CharField(
        max_length = 100, 
        choices = SUBJECTS.choices,
        default = SUBJECTS.RENT
    )
    type = models.CharField(
        max_length = 100, 
        choices = TYPES.choices,
        default = TYPES.CREDIT
    )
    status = models.CharField(
        max_length = 100, 
        choices = STATUES.choices,
        default = STATUES.PENDING
    )
    amount = models.DecimalField(max_digits = 10, decimal_places = 2)
    bill_url = models.URLField(
        _("Payment URL"),
        blank = True,null = False
    )

    # META CLASS
    class Meta:
        ''' Meta class for Transaction Model. '''

        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ['-created']
        # abstract = True

    def __str__(self):
        return self.code

    def get_id_prefix(self):
        return 'TRANS'

    def format_order(self):
        ''' Return an Order Json fromTransaction. '''
        raise NotImplementedError(
            'Transaction class must Override format_order method.'
        )
    
    def set_amount(self,amount):
        ''' Updates Transaction amount. '''

        self.amount = amount
        self.save()

    def set_bill_url(self,url):
        ''' Update transaction billurl '''
        self.bill_url = url
        self.save()

    def get_bill_url(self):
        ''' Return bill_url. '''
        ''' Can implement custom logics here before returning bill_url. '''

        return self.bill_url

    def refund(self):
        ''' All SubClasses must implement this method. '''

        raise NotImplementedError(
            'Every Transaction subclass must implement refund method.'
        )
    
    def succed(self):
        ''' Change transaction status to success. '''

        self.status = self.STATUES.SUCCESS
        self.save()

    def fail(self):
        ''' Change transaction status to failure. '''

        self.status = self.STATUES.FAILURE
        self.save()


####
##     RECHARGE TRANSACTION MODEL
#####
class RechargeTransaction(Transaction):
    ''' Store informations about Recharge Transactions. '''

    user = models.ForeignKey(
        User,on_delete = models.CASCADE,
        related_name = "recharge_transactions"
    )
    is_called_back = models.BooleanField(default = False)

    # META CLASS
    class Meta:
        ''' Meta class for Transaction Model. '''

        verbose_name = _("Recharge Transaction")
        verbose_name_plural = _("Recharge Transactions")
        ordering = ['-created']

    def get_id_prefix(self):
        return 'R' + super().get_id_prefix()

    def clean(self):
        ''' Override clean method. '''

        # ENSURE "self.type" IS CREDIT
        self.type = self.TYPES.CREDIT

        # ENSURE "self.subject" IS RECHARGE
        self.subject = self.SUBJECTS.RECHARGE

        super().clean()

    def format_order(self):
        ''' Return a self formated Json order fot Payment. '''
        return {
            'amount':int(round(self.amount)),
            'merchant_reference':str(self.id),
            'call_back_url':f'{get_host_url()}/billings/recharges/{self.id}',
            'client':{
                'first_name':self.user.first_name,
                'last_name':self.user.last_name,
                'phone':str(self.user.phone_number),
            }
        }
        
    def get_call_back_url(self):
        ''' Return Transaction call back url. '''
        return f'{get_host_url()}/billings/transactions/recharges/{self.id}'
    
    def get_wallet(self):
        ''' return active working wallet. '''

        return self.user.wallet
    
    def succed(self):
        ''' Change transaction status to success. '''

        self.get_wallet().credit(self.amount)
        super().succed()


