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
        'code','subject','type','amount',
        'status'
    )
    list_filter = (
        'type','subject','status'
    )
    search_fields = (
        'code',
    )
    list_per_page = LIMIT_PER_PAGE
