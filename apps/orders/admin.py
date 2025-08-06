from django.contrib import admin

from apps.orders.models import (
    Order
)

# Register your models here.

LIMIT_PER_PAGE = 100


####
##      ORDERS ADMIN SITE
#####
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    ''' Admin site configs for Orders Model. '''
    
    list_display = [
        'code','client','is_validated',
        'is_paid','created'
    ]
    list_filter = [
        'is_validated','is_paid',
    ]
    search_fields = [
        'code','client','articles'
    ]
    list_per_page = LIMIT_PER_PAGE