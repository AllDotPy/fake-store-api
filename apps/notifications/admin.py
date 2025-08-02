from django.contrib import admin

from apps.notifications.models import (
    Notification,NotificationService,
    ReminderSettings
)

# Register your models here.

LIMIT_PER_PAGE = 100

####
##      GENERIC NOTIFICATION SERVICE ADMIN CLASS
#####
@admin.register(NotificationService)
class NotificationServiceAdmin(admin.ModelAdmin):
    ''' Admin site configs for Notification Service Model. '''
    
    list_display = [
        'code','name','description','type','is_active','created'
    ]
    list_filter = [
        'type','is_active'
    ]
    search_fields = [
        'code','name','description'
    ]
    limit_per_page = LIMIT_PER_PAGE
    
    actions = ['activate','deactivate']
    
    def activate(self, request, queryset):
        """ Action to set the notification service as active. """
        
        for obj in queryset:
            obj.activate()
            
    def deactivate(self, request, queryset):
        """ Action to set the notification service as inactive. """
        
        for obj in queryset:
            obj.deactivate()
            
    activate.short_description = 'Activate Service'
    deactivate.short_description = 'Deactivate Service'
    
    
####
##      GENERIC NOTIFICATION ADMIN CLASS
#####
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    ''' Admin site configs for Notifications Model. '''
    
    list_display = [
        'code','user','title','message',
        'service','created'
    ]
    list_filter = [
        'service'
    ]
    search_fields = [
        'code','title','message'
    ]
    limit_per_page = LIMIT_PER_PAGE
    
    
####
##      GENERIC NOTIFICATION REMINDER SETTING ADMIN CLASS
#####
@admin.register(ReminderSettings)
class ReminderSettingAdmin(admin.ModelAdmin):
    ''' Admin site configs for Reminder Settings Model. '''
    
    list_display = [
        'code','user','service','frequency',
        'start_time','created'
    ]
    list_filter = [
        'service'
    ]
    search_fields = [
        'code',
    ]
    limit_per_page = LIMIT_PER_PAGE