from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from easyswitch import (
    TransactionDetail, CustomerInfo, Provider,
    TransactionStatus, Currency, TransactionType
)

from apps.utils.models import TimeStampedUUIDModel
from apps.accounts.models import User
from core.exceptions import PaymentInitiationError

# Create your models here.
    
####
##       BASE TRANSACTION MODEL
#####
class Transaction(TimeStampedUUIDModel):
    ''' Store informations about Transactions for Store. '''

    # STATUES CHOICES
    class STATUES(models.TextChoices):
        ''' Transaction statues. '''

        PENDING = 'PENDING', _('PENDING')
        SUCCESSFUL = 'SUCCESSFUL', _('SUCCESSFUL')
        FAILED = 'FAILED', _('FAILED')
        CANCELLED = 'CANCELLED', _('CANCELLED')
        REFUNDED = 'REFUNDED', _('REFUNDED')
    
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
        CINEPAY = 'CINEPAY', _('CINEPAY')
        PAYGATE = 'PAYGATE', _('PAYGATE')
        FEDAPAY = 'FEDAPAY', _('FEDAPAY')
    
    # TYPES CHOICES
    class TYPES(models.TextChoices):
        ''' Transaction types. '''

        PAYMENT = 'PAYMENT',_('PAYMENT')
        REFUND = 'REFUND',_('REFUND')
        
    # RELATIONSHIPS
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_("User")
    )
    
    # ORDER RELATIONSHIP (for shop)
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_("Order")
    )
    
    status = models.CharField(
        max_length = 100, 
        choices = STATUES.choices,
        default = STATUES.PENDING
    )
    amount = models.DecimalField(max_digits = 10, decimal_places = 2)
    currency = models.CharField(
        max_length = 25,
        choices = CURRENCIES.choices,
        default=settings.EASYSWITCH_CURRENCY
    )
    provider = models.CharField(
        max_length = 100,
        choices = PROVIDERS.choices,
    )
    type = models.CharField(
        max_length = 100,
        choices = TYPES.choices,
    )
    payment_link = models.URLField(
        _("Payment URL"),
        blank = True, null = True
    )
    description = models.TextField(
        blank = True, null = True,
        verbose_name=_("Description")
    )
    
    # PAYMENT METHOD
    payment_method = models.CharField(
        max_length = 50,
        blank = True, null = True,
        verbose_name=_("Payment Method")
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

    def get_payment_link(self):
        ''' Return payment_link. '''
        ''' Can implement custom logics here before returning payment_link. '''

        return self.payment_link

    def set_provider(self, reference):
        ''' Set provider reference. '''
        self.provider_reference = reference
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
        # TODO: Implement callback URL logic
        return f"/api/billings/callback/{self.code}/"
        
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
            first_name=self.user.first_name if self.user.first_name else None,
            last_name=self.user.last_name if self.user.last_name else None,
            email=self.user.email if self.user.email else None,
            address=getattr(self.user, 'address', None),
            city=getattr(self.user, 'city', None),
            country=getattr(self.user, 'country', None),
            postal_code=getattr(self.user, 'postal_code', None),
            zip_code=getattr(self.user, 'zip_code', None),
            state=getattr(self.user, 'state', None),
            id=str(self.user.id),
        )
    
    def to_easyswitch_transaction_detail(self) -> TransactionDetail:
        ''' Prepares TransactionDetail data according to the EasySwitch structure. '''

        return TransactionDetail(
            transaction_id=self.code,
            provider=Provider(self.provider),
            status=TransactionStatus(self.status),
            currency=Currency(self.currency),
            amount=float(self.amount),
            transaction_type=TransactionType(self.type),
            reason=self.description or f'Payment for transaction {self.code}',
            callback_url=self.get_callback_url(),
            reference=self.code,  # ou une référence personnalisée
            customer=self.to_easyswitch_customer_info(),
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
