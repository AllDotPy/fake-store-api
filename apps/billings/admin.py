from django.contrib import admin
from apps.billings.models import (
    Transaction,
)

# Register your models here.

LIMIT_PER_PAGE=100
  
####
##      GENERIC TRANSACTIONS ADMIN CLASS
#####
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    ''' Admin site configs for Transaction Model. '''

    list_display = (
        'code','type','amount',
        'status', 'payment_link', 'created', 'modified'
    )
    list_filter = (
        'type','status'
    )
    search_fields = (
        'code',
    )
    list_per_page = LIMIT_PER_PAGE
