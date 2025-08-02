from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,IsAdminUser
)

from apps.notifications.serializers import (
    NotificationServiceSerializer,
    ReminderSettingsSerializer,
    NotificationSerializer,
)
from apps.utils.functions import get_object_or_None

# Create your views here.


####
##      NOTIFICATION SERVICE VIEWSET CLASS
#####
class NotificationServiceViewSet(ModelViewSet):
    ''' Viewset class for NotificationService Model. '''

    queryset = NotificationServiceSerializer.Meta.model.objects.all()
    serializer_class = NotificationServiceSerializer
    permission_classes = [IsAuthenticated,IsAdminUser]
    lookup_field = 'id'
    

####
##      NOTIFICATION VIEWSET CLASS
#####
class NotificationViewSet(ModelViewSet):
    ''' Viewset class for Notification Model. '''

    queryset = NotificationSerializer.Meta.model.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated,IsAdminUser]
    search_fields = ['title','message']
    lookup_field = 'id'

    def get_queryset(self):
        ''' Return a specific queryset objects based on user. '''

        # ADMIN OR STAFF USERS
        usr = self.request.user
        if usr.is_staff or usr.is_superuser:
            return self.queryset
        
        return self.queryset.filter(
            user = usr
        )
        
    def get_permissions(self):
        ''' Define a way to use permissions based on action. '''
        
        # LIST ACTION
        if self.action in ('list','mark_as_read'):
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    @action(methods=['PUT'],detail=True)
    def mark_as_read(self,request,id):
        ''' Mark a notification object as read '''
        
        # ENSURE NOTIFICATION OBJECT WITH UUID "pk" EXISTS!
        obj = get_object_or_None(
            self.serializer_class.Meta.model,id=id
        )
        
        if obj is not None:
            # COOL! MARK AS READ AND SAVE THE INSTANCE
            obj.mark_as_read()
            
            return Response(
                {
                    'status':'Success',
                    'message':{
                        'en': f'Notification "{obj.id}" has been marked as Read',
                        'fr': f'Notification marquée comme lue.'
                    }
                }
            )
            
        # NOTIFICATION DOES NOT EXIST!
        return Response(
            {
                'status':'error',
                'message':{
                    'en': f'Notification With uuid {id} does not exist.',
                    'fr': 'Aucun objet notification trouvé pour ces informations'
                }
            },
            status = 404
        )
    

####
##      REMINDER SETTINGS VIEWSET CLASS
#####
class ReminderSettingViewSet(ModelViewSet):
    ''' Viewset class for Notification Model. '''

    queryset = ReminderSettingsSerializer.Meta.model.objects.all()
    serializer_class = ReminderSettingsSerializer
    permission_classes = [IsAuthenticated,IsAdminUser]
    lookup_field = 'id'

    def get_queryset(self):
        ''' Return a specific queryset objects based on user. '''

        # ADMIN OR STAFF USERS
        if self.request.user.is_staff:
            return self.queryset
        
        return self.queryset.filter(
            user = self.request.user
        )