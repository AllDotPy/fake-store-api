import resend
import firebase_admin
from server.settings import EMAIL_HOST_USER
from twilio.rest import Client
from django.core.mail import send_mail
from firebase_admin import credentials, messaging
from infobip_channels.sms.channel import SMSChannel

import firebase_admin
from firebase_admin import credentials
from firebase_admin.firestore import firestore

from apps.notifications.models import(
    Notification,
)



####
##      NOTIFICATION SERVICE CLASS
#####
class NotificationService():
    ''' Notification Service. '''

    def call_send_functions(self,suffix,**options):
        ''' call functions based on suffix '''

        function_name = 'send_' + suffix

        # CHECK IF A FUNCTION "function_name" EXISTS AND IS CALLABLE
        if hasattr(self, function_name) and callable(getattr(self, function_name)):
            # THEN CALL IT WITH ARGUMENT
            getattr(self, function_name)(**options)

        # RAISE EXCEPTION ELSE
        else:
            raise ValueError(
                f'No member named send_{suffix} or invalid notification service type.'
            )

    def send_whatsapp_message(self,message,_to=''):
        ''' Send Whatsapp message to a given phone number. '''

        m = self.client.messages.create(
            to=f"whatsapp:{_to}", 
            from_=f"whatsapp:{self.SERVICE_PHONE_NUMBER}", 
            body=message
        )

    def send_sms(self, notification:Notification):
        """ Send SMS message with Twilio API. """
        
        # GET PREFIX FROM SERVICE NAME
        prefix = notification.service.name.lower()
        
        return SmsServices().call_service(
            prefix = prefix,notification = notification
        )

    def send_push_notification(self,notification:Notification):
        ''' Send a push notification to a given user. '''
        
        # GET PREFIX FROM SEVICE NAME
        prefix = notification.service.name.lower()
        
        return PushServices().call_service(
            prefix = prefix,notification = notification
        )

    def send_email(self,notification:Notification):
        ''' Send an email notification. '''

        # GET PREFIX FROM SERVICE NAME
        prefix = notification.service.name.lower()
        
        return EmailServices().call_service(
            prefix = prefix,notification = notification
        )

    def send_notification(self,notification:Notification):
        ''' Send notification function. '''

        # SEND NOTIFICATION ACCORDING TO SERVICE
        self.call_send_functions(
            notification.service.type.lower().replace(' ','_'),
            notification = notification
        )
        
        
####
##      BASE SERVICE CLASS
#####
class BaseService():
    ''' Base class for all service classes. '''
    
    def get_suffix(self):
        ''' Return the service suffix. '''
        
        raise NotImplementedError("Subclasses must implement this method.")
    
    def call_service(self,prefix,**options):
        ''' call functions based on prefix '''

        function_name = prefix + self.get_suffix()

        # CHECK IF A FUNCTION "function_name" EXISTS AND IS CALLABLE
        if hasattr(self, function_name) and callable(getattr(self, function_name)):
            # THEN CALL IT WITH ARGUMENT
            getattr(self, function_name)(**options)

        # RAISE EXCEPTION ELSE
        else:
            raise ValueError(
                f'No member named {prefix}{self.get_suffix()} or invalid notification service type.'
            )


####
##      SMS SERVICES CLASS
#####
class SmsServices(BaseService):
    ''' Provides SMS services functionality. '''
    
    def get_suffix(self):
        ''' Return the suffix for the service. '''
        return '_sms'
    
    def twilio_sms(self,notification:Notification):
        ''' Send a twilio SMS message. '''
        
        try:
            config = notification.service.load_configs()
            account_sid = config['ACCOUNT_ID']  
            auth_token = config['AUTHTOKEN']  
            client = Client(account_sid, auth_token)

            message = client.messages.create(
                messaging_service_sid = config['SERVICE_SID'],  
                body = notification.message,
                to = str(notification.user.phone_number),
            )
            
            return True
        except Exception as e:
            print(f"SMS MESSAGE SENDER ERROR: {str(e)}")
            return False
        
    def infobip_sms(self,notification:Notification):
        ''' Send a InfoBip SMS message. '''
        
        try:
        
            # LOAD SERVICES CONFIGURATIONS FIRST
            configs = notification.service.load_configs()
            
            # CREATE MESSAGE SERVICE CHANNEL.
            channel = SMSChannel.from_auth_params(
                configs
            )
            
            # SEND MESSAGE
            sms_response = channel.send_sms_message(
                {
                    "messages": [{
                        "destinations": [{
                            "to": str(notification.user.phone_number),
                        }],
                        "from": "Learnia",
                        "text": notification.message
                    }]
                }
            )
            return True if sms_response else False
        except Exception as e:
            print(e)
            return False
        
        
####
##      SMS SERVICES CLASS
#####
class PushServices(BaseService):
    ''' Provides methods to send notifications through push services. '''
    
    def get_suffix(self):
        """ Returns the service name suffix. """
        return '_push'
    
    def firebase_push(self,notification:Notification):
        ''' Send a Firebase Cloud Messaging (FCM). '''
        
        try:
            # LOAD CONFGS
            config = notification.service.load_configs()

            # INITIALIZE FIREBASE APP
            cred = credentials.Certificate(config)
            try:
                firebase_admin.initialize_app(cred)
            except:pass

            # GET TOKENS
            tokens = notification.user.load_fcm_tokens()

            # THEN SEND NOTIFICATIONS TO ALL RELATED AND CONNECTED DEVICES
            for k,v in tokens:
                # CREATE OUR MESSAGE
                message = messaging.Message(
                    notification = messaging.Notification(
                        title = notification.title,
                        body=notification.message,
                        # image='https://storage.googleapis.com/dreammore_1/DM_APP_LOGO/DREAMORE_APP_LOGO_EXE_.png'
                    ),
                    token = v,
                )

                # SEND THE NOIFICATION
                response = messaging.send(message)

            return True
        except Exception as e:
            print(e)
            return False
        
        
####
##      EMAIL SERVICES CLASS
#####
class EmailServices(BaseService):
    ''' Provide method to send email messages. '''
    
    def get_suffix(self):
        ''' Return the service name suffix. '''
        return '_email'
    
    def django_email(self,notification:Notification):
        ''' Send a notification to user using Django email. '''
        
        try:
            # SEND EMAIL
            send_mail(
                notification.title, 
                notification.message, 
                EMAIL_HOST_USER, 
                [notification.user.email], 
                fail_silently=False
            )
            return True
        except Exception as e:
            print(e)
            return False
        
    def resend_email(self,notification:Notification):
        ''' Resend an already sent email notification. '''
        
        try:
            # LOAD CONFIG FIRST
            config = notification.service.load_configs()
            resend.api_key =  config['API_KEY']
            params = {
                "from": "verify@dreammore.co",
                "to": [notification.user.email],
                "subject": notification.title,
                "html": notification.message,
            }

            # SEND EMAIL
            email = resend.Emails.send(params)
            return True if email else False
        except Exception as e:
            print(e)
            return False