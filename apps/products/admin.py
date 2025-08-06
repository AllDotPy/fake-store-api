from django.contrib import admin

from apps.products.models import (
    Product, ProductMedia
)

# Register your models here.

LIMIT_PER_PAGE = 100


#####
##      GENERIC PRODUCT MEDIA IN LINE CLASS
######
class ProductMediaInline(admin.TabularInline):
    ''' Inline class for Product Media Model Admin '''
    model = ProductMedia
    extra = 1


####
##      PRODUCTS ADMIN SITE
#####
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    ''' Admin site configs for Products Model. '''
    
    list_display = [
        'code','name','category',
        'price','tva','created'
    ]
    list_filter = [
        'category'
    ]
    search_fields = [
        'code','name','description'
    ]
    inlines = [
        ProductMediaInline
    ]
    list_per_page = LIMIT_PER_PAGE