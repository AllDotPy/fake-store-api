from django.contrib import admin

from apps.orders.models import (
    Order, Article
)

# Register your models here.

LIMIT_PER_PAGE = 100


#####
##      GENERIC PRODUCT MEDIA IN LINE CLASS
######
class ArticleInline(admin.TabularInline):
    ''' Inline class for Article Model Admin '''
    model = Article
    extra = 1


####
##      ORDERS ADMIN SITE
#####
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    ''' Admin site configs for Orders Model. '''
    
    list_display = [
        'code','client',
        'status','created'
    ]
    list_filter = [
        'status',
    ]
    search_fields = [
        'code','client','articles'
    ]
    list_per_page = LIMIT_PER_PAGE
    inlines = [ArticleInline]
