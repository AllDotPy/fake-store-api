""" This module is our homemade SDK responsible for Managing SMS services via infobip. """

from py3_infobip import (
    SmsClient,
    SmsTextSimpleBody
)


####
##      INFOBIP SMS MANAGER CLASS
#####
class MessageManager(object):
    ''' Infobip Manager class. '''
    
    def __init__(self):
    
        self.infobip_client = SmsClient(
                api_key = "96f83ac9cf23ed1550a7af75a9202dac-e36db9aa-d1ab-4747-bcd1-57349f97b742",
                url = "w1mkkd.api.infobip.com"
        )
        
    def send_sms(self,msg,_to:str):
        ''' send a message to the a given phone number. '''
        message = SmsTextSimpleBody()
        message \
            .set_to([
            _to
        ]) \
            .set_text(msg)
        
        sms_response = self.infobip_client.send_sms_text_simple(message)
        
        return sms_response