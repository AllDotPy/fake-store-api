from rest_framework.serializers import ModelSerializer

from apps.notifications.models import (
    NotificationService, Notification,
    ReminderSettings
)
from apps.accounts.serializers import (
    UserSerializer
)

####
##      NOTIFICTATION SERVICE SERIALIZER CLASS
#####
class NotificationServiceSerializer(ModelSerializer):
    ''' Serializer class for Notification Service Model. '''

    # META CLASS
    class Meta:
        ''' Meta class for NotificationServiceSerializer. '''
        model = NotificationService
        fields = '__all__'

    def to_representation(self, instance:NotificationService):
        ''' Override representation method to add customized fields. '''

        # FIRST GET INSTANCE REPRESENTATION
        rep = super().to_representation(instance)

        # LOAD CONFIGURATIONS
        config = instance.load_configs()

        # ADD FIELDS TO THE REP
        rep |= {'configuration':config}

        return rep
    

####
##      NOTIFICTATION SERIALIZER CLASS
#####
class NotificationSerializer(ModelSerializer):
    ''' Serializer class for Notification Model. '''

    # META CLASS
    class Meta:
        ''' Meta class for NotificationSerializer. '''
        model = Notification
        fields = '__all__'

    def to_representation(self, instance:Notification):
        ''' Override representation method to add customized fields. '''

        # FIRST GET INSTANCE REPRESENTATION
        rep = super().to_representation(instance)

        # ADD RELATED USER
        user = UserSerializer(
            instance = instance.user
        ).data
        # ADD RELATED SERVICE TOO
        service = NotificationServiceSerializer(
            instance = instance.service
        ).data

        # ADD FIELDS TO THE REP
        rep |= {'user':user,'service':service}

        return rep
    

####
##      NOTIFICTATION REMINDER SERIALIZER CLASS
#####
class ReminderSettingsSerializer(ModelSerializer):
    ''' Serializer class for Reminder Settings Model. '''

    # META CLASS
    class Meta:
        ''' Meta class for ReminderSettingsSerializer. '''
        model = ReminderSettings
        fields = '__all__'

    def to_representation(self, instance:ReminderSettings):
        ''' Override representation method to add customized fields. '''

        # FIRST GET INSTANCE REPRESENTATION
        rep = super().to_representation(instance)

        # ADD RELATED USER
        user = UserSerializer(
            instance = instance.user
        ).data
        # ADD RELATED SERVICE TOO
        service = NotificationServiceSerializer(
            instance = instance.service
        ).data

        # ADD FIELDS TO THE REP
        rep |= {'user':user,'service':service}

        return rep