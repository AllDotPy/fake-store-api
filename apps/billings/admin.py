from django.contrib import admin
from apps.billings.models import (
    Wallet, Transaction, RechargeTransaction,
)

# Register your models here.

LIMIT_PER_PAGE=100

####
##      GENERIC WALLET ADMIN CLASS
#####
@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    ''' Admin site configs for Wallet Model. '''

    list_display = (
        'code','user','balance','created'
    )
    search_fields = (
        'code','created'
    )
    list_per_page = LIMIT_PER_PAGE
    
    
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
    
    
####
##      GENERIC TRANSACTIONS ADMIN CLASS
#####
@admin.register(RechargeTransaction)
class RechargeTransactionAdmin(admin.ModelAdmin):
    ''' Admin site configs for Transaction Model. '''

    list_display = (
        'code','user','amount','subject','type',
        'status'
    )
    list_filter = (
        'type','subject','status'
    )
    search_fields = (
        'code',
    )
    list_per_page = LIMIT_PER_PAGE
