import time, random
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from easyswitch import (
    TransactionDetail, CustomerInfo, Provider,
    TransactionStatus, Currency, TransactionType
)

from apps.orders.models import Order
from apps.utils.models import TimeStampedUUIDModel
from apps.accounts.models import User
from core.exceptions import PaymentInitiationError

# from apps.utils.functions import get_host_url

# Create your models here.
    
####
##       BASE TRANSACTION MODEL
#####
class Transaction(TimeStampedUUIDModel):
    ''' Store informations about Transactions for Store. '''

    # STATUES CHOICES
    class STATUES(models.TextChoices):
        ''' Transaction statues. '''

        PENDING = 'pending', _('PENDING')
        SUCCESSFUL = 'successful', _('SUCCESSFUL')
        FAILED = 'failed', _('FAILED')
        CANCELLED = 'cancelled', _('CANCELLED')
        REFUNDED = 'refunded', _('REFUNDED')
    
    # CURRENCIES
    class CURRENCIES(models.TextChoices):
        ''' Transaction currencies. '''

        XOF = 'XOF', _('XOF')  # Franc CFA (BCEAO)
        XAF = 'XAF', _('XAF')  # Franc CFA (BEAC)
        NGN = 'NGN', _('NGN')  # Naira nigérian
        GHS = 'GHS', _('GHS')  # Cedi ghanéen
        EUR = 'EUR', _('EUR')  # Euro
        USD = 'USD', _('SUD')  # Dollar américain
        CDF = 'CDF', _('CDF')  # Franc congolais
        GNF = 'GNF', _('GNF')  # Franc guinéen
        KMF = 'KMF', _('KMF')  # Franc comorien
    
    # PROVIDERS CHOICES
    class PROVIDERS(models.TextChoices):
        ''' Transaction providers. '''

        SEMOA = 'SEMOA', _('SEMOA')
        BIZAO = 'BIZAO', _('BIZAO')
        CINETPAY = 'CINETPAY', _('CINETPAY')
        PAYGATE = 'PAYGATE', _('PAYGATE')
        FEDAPAY = 'FEDAPAY', _('FEDAPAY')
    
    # TYPES CHOICES
    class TYPES(models.TextChoices):
        ''' Transaction types. '''

        PAYMENT = 'payment',_('PAYMENT')
        REFUND = 'refund',_('REFUND')
        
    # RELATIONSHIPS
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_("User")
    )
    
    # ORDER RELATIONSHIP (for store)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_("Order")
    )
    
    status = models.CharField(
        max_length=100, 
        choices=STATUES.choices,
        default=STATUES.PENDING
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(
        max_length=25,
        choices=CURRENCIES.choices,
        default=settings.EASYSWITCH_CURRENCY
    )
    provider = models.CharField(
        max_length=100,
        choices=PROVIDERS.choices,
        default=PROVIDERS[str(settings.EASYSWITCH_DEFAULT_PROVIDER).upper()]
    )
    type = models.CharField(
        max_length=100,
        choices=TYPES.choices,
        default=TYPES.PAYMENT
    )
    payment_link = models.URLField(
        verbose_name=_("Payment URL"),
        blank=True, null=True,
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
    )
    is_called_back = models.BooleanField(default=False)
    
    # PAYMENT METHOD
    payment_method = models.CharField(
        verbose_name=_("Payment Method"),
        max_length=50,
        blank=True, null=True,
    )

    # META CLASS
    class Meta:
        ''' Meta class for Transaction Model. '''

        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ['-created']

    def __str__(self):
        return self.code

    def get_id_prefix(self):
        return 'TRANS'
    
    def set_amount(self, amount):
        ''' Updates Transaction amount. '''
        self.amount = amount
        self.save()

    def set_payment_link(self, url):
        ''' Update transaction payment_link '''
        self.payment_link = url
        self.save()
    
    def set_statuse(self, status):
        ''' Update transaction status '''
        self.status = status
        self.save()
    
    def set_reference(self, reference):
        ''' Update transaction reference '''
        self.reference = reference
        self.save()

    def get_payment_link(self):
        ''' Return payment_link. '''
        ''' Can implement custom logics here before returning payment_link. '''

        return self.payment_link
    
    def get_reference(self):
        ''' Return reference '''
        
        return self.reference

    def set_provider(self, provider):
        ''' Set provider reference. '''
        self.provider = provider
        self.save()
    
    def succeed(self):
        ''' Change transaction status to successful. '''
        self.status = self.STATUES.SUCCESSFUL
        self.save()

    def fail(self):
        ''' Change transaction status to failure. '''
        self.status = self.STATUES.FAILED
        self.save()
        
    def cancel(self):
        ''' Change transaction status to cancelled. '''
        self.status = self.STATUES.CANCELLED
        self.save()

    def get_callback_url(self):
        ''' Return callback URL for payment provider. '''
        
        # callback_url = f"{settings.EASYSWITCH_FEDAPAY_CALLBACK_URL}?id={self.id}/callback"
        callback_url = f"{settings.EASYSWITCH_FEDAPAY_CALLBACK_URL}callback"
        return callback_url
        
    def is_paid(self):
        ''' Check if transaction is paid. '''
        return self.status == self.STATUES.SUCCESSFUL
        
    def can_refund(self):
        ''' Check if transaction can be refunded. '''
        return self.status == self.STATUES.SUCCESSFUL
    

    def to_easyswitch_customer_info(self) -> CustomerInfo:
        ''' Prepares CustomerInfo data according to the EasySwitch structure. '''

        return CustomerInfo(
            phone_number=str(self.user.phone_number),
            first_name=self.user.first_name,
            last_name=self.user.last_name,
            # email=self.user.email if self.user.email else '', # FedaPay doesn't support many customer with same email
            # address=getattr(self.user, 'address', ''),
            # city=getattr(self.user, 'city', ''),
            # country=getattr(self.user, 'country', ''),
            # postal_code=getattr(self.user, 'postal_code', ''),
            # zip_code=getattr(self.user, 'zip_code', ''),
            # state=getattr(self.user, 'state', ''),
            # id=str(self.user.id),
        )
    
    def to_easyswitch_transaction_detail(self) -> TransactionDetail:
        ''' Prepares TransactionDetail data according to the EasySwitch structure. '''

        return TransactionDetail(
            transaction_id=self.code,
            provider=Provider(self.provider),
            status=TransactionStatus(self.status),
            currency=Currency(self.currency),
            amount=int(self.amount),
            transaction_type=TransactionType(self.type),
            callback_url=self.get_callback_url(),
            reference=self.code,
            customer=self.to_easyswitch_customer_info(),
            reason=f"Payment for order",
            metadata={
                "Transaction": str(self.code)
            }
        )
    
    def to_easyswitch_format(self) -> TransactionDetail:
        ''' Main method to export to EasySwitch format. '''

        self.validate_for_easyswitch()
        return self.to_easyswitch_transaction_detail()
    
    def validate_for_easyswitch(self) -> bool:
        ''' Main method to export to EasySwitch format. '''

        errors = []
        
        # Validation CustomerInfo selon EasySwitch        
        if not self.user.phone_number:
            errors.append("Customer phone_number is required for EasySwitch")
        
        # Validation TransactionDetail
        if self.amount <= 0:
            errors.append("Amount must be greater than 0")
        
        if not self.code:
            errors.append("Transaction code is required")
        
        if errors:
            raise PaymentInitiationError(f"Transaction validation failed: {'; '.join(errors)}")
        
        return True

    def generate_code(self):
        """ Generate unique code for Transaction. """
        
        timestamp = int(time.time())  # seconds since 1970 (10 digits in 2025)
        rand = random.randint(10, 99) # 2 random numbers
        return int(f"{timestamp}{rand}") % (10**11)  # truncate to 11 digits
