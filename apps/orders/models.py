from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.utils.models import TimeStampedUUIDModel
from apps.products.models import (
    Product,
)
from apps.accounts.models import (
    User
)


# Create your models here.


####
##      ORDER MODEL
#####
class Order(TimeStampedUUIDModel):
    ''' Store information about Order. '''
    
    class OrderStatus(models.TextChoices):
        ''' Transaction statues. '''

        WAITING_FOR_PAYMENT = 'waiting', _('WAITING FOR PAYMENT')
        DELIVERING = 'delivering', _('DELIVERING')
        COMPLETED = 'completed', _('COMPLETED')
    
    client = models.ForeignKey(
        User, on_delete = models.CASCADE,
        null = False, blank = False,
        related_name = 'orders'
    )
    status = models.CharField(
        max_length=100, 
        choices=OrderStatus.choices,
        default=OrderStatus.WAITING_FOR_PAYMENT
    )
    
    # META CLASS
    class Meta:
        ''' Meta class for Order Model '''
        
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created']
    
    def __str__(self):
        return self.code
    
        
    def get_id_prefix(self):
        ''' Return a specific ID prefix for Articles Model Objects. '''
        return 'ORDER'
    
    def total(self):
        ''' Return the order total price. '''
        
        # NORMALY WILL RETURN A REULT OF (selling_prince * quantity)
        return sum([a.total() for a in self.articles.all()])


####
##      ORDERING PRODUCTS MODEL
#####
class Article(TimeStampedUUIDModel):
    ''' Store information about Order Articles. '''
    
    order = models.ForeignKey(
        Order, on_delete = models.CASCADE,
        related_name = 'articles',
        null = False, blank = False
    )
    product = models.ForeignKey(
        Product, on_delete = models.CASCADE,
        related_name = 'articles',
        null = False, blank = False
    )
    selling_price = models.IntegerField(default = 0)
    quantity = models.IntegerField(default=1)         # WOULD LIKE TO ADD QUANTITY.
    
    # META CLASS
    class Meta:
        ''' Meta class for Ordering Article Model '''
        
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')
        ordering = ['created']
    
    def __str__(self):
        return self.product.name
    
        
    def get_id_prefix(self):
        ''' Return a specific ID prefix for Articles Model Objects. '''
        return 'ART'
    
    def total(self):
        ''' Return the article total price. '''
        
        # NORMALY WILL RETURN A RESULT OF (selling_prince * quantity)
        return self.selling_price * self.quantity
