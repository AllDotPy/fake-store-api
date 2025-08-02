import simplejson as Json
from django.db import models
from bson.objectid import ObjectId
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import(
    User,
)
from apps.utils.models import (
    TimeStampedUUIDModel
)

# Create your models here.

####
##      NOTIFICATION SERVICE MODEL
#####
class NotificationService(TimeStampedUUIDModel):
    ''' Store informations about Notification services. '''

    # SERVICE TYPE CHOICES
    class TYPES(models.TextChoices):
        ''' Service type available choices. '''
        
        EMAIL = 'EMAIL', _('EMAIL')
        SMS = 'SMS', _('SMS')
        FIRESTORE = 'FIRESTORE',_('FIRESTORE')
        PUSH_NOTIFICATIONS = 'PUSH_NOTIFICATION', _('PUSH NOTIFICATION')

    name = models.CharField(max_length = 100)
    description = models.CharField(max_length = 250)
    type = models.CharField(
        max_length = 20,choices=TYPES.choices,
        default=TYPES.PUSH_NOTIFICATIONS
    )
    configuration = models.TextField(default = '{}')
    is_active = models.BooleanField(default = False)

    # META CLASS
    class Meta:
        ''' Meta class for Notification Service Model. '''

        verbose_name = _("Notification Service")
        verbose_name_plural = _("Notification Service")
        ordering = ['-created']

    def __str__(self):
        return self.name

    def get_id_prefix(self):
        return 'NS'

    def clean(self):
        ''' Clean data before saving. '''

        # ENSURE THE VALUE OF CONFIG FIELD IS A VALID JSON 
        self.load_configs(raise_exception=True)

        super().clean()

    def load_configs(self,raise_exception=False):
        ''' Return a Python dict object from a Json string. '''

        try:
            return Json.loads(self.configuration)
        except:
            if raise_exception:
                raise ValidationError(
                    f"Invalid JSON Configuration in {self.__class__.__name__}"
                )
            return {}
        
    def activate(self):
        ''' Mark the current Service as Active for Type. '''
        
        # GET ALL SERVICES WITH SAME TYPE AND DEACTIVATE THEM
        ns = NotificationService.objects.filter(type = self.type)
        for n in ns:
            n.deactivate()
            
        # MARK ITSELF AS ACTIVE
        self.is_active = True
        self.save()
            
    def deactivate(self):
        ''' Deactivate service. '''
        
        self.is_active = False
        self.save()


####
##      NOTIFICATION MODEL
#####
class Notification(TimeStampedUUIDModel):
    ''' Store informations about Notifications. '''

    user = models.ForeignKey(
        User,null = False,blank = True,
        on_delete = models.CASCADE,
        related_name = 'notifications'
    )
    title = models.CharField(max_length = 150,default = 'New notification.')
    message = models.TextField(default = 'No message yet!')
    service = models.ForeignKey(
        NotificationService,null=False,
        on_delete = models.CASCADE,
        blank = True,related_name = 'notifications',
    )
    is_readed = models.BooleanField(default=False)

    # META CLASS
    class Meta:
        ''' Meta class for Notification Service Model. '''

        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-created','-is_readed']

    def __str__(self):
        return self.code

    def get_id_prefix(self):
        return 'NOT'
    
    def mark_as_read(self):
        ''' Mark object as read. '''
        
        self.is_readed = True
        self.save()


####
##      REMINDER SETTINGS MODEL
#####
class ReminderSettings(TimeStampedUUIDModel):
    ''' Store informations about Reminder Settings. '''

    user = models.ForeignKey(
        User,null = False, blank = True,
        on_delete = models.CASCADE,
        related_name = 'reminders'
    )
    service = models.ForeignKey(
        NotificationService, null = False,
        on_delete = models.CASCADE,
        blank = True, related_name = 'reminders',
    )
    frequency = models.DurationField()
    start_time = models.DateTimeField()

    # META CLASS
    class Meta:
        ''' Meta class for Notification Service Model. '''

        verbose_name = _("Reminder Setting")
        verbose_name_plural = _("Reminder Settings")
        ordering = ['-created']

    def __str__(self):
        return self.code

    def get_id_prefix(self):
        return 'RMD'