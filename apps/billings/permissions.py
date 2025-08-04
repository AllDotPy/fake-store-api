from rest_framework import permissions


####
##      IS PAYMENT API PROVIDER PERMISSIONS CLASS
#####
class IsPaymentApiProvider(permissions.BasePermission):
    ''' Custom Permission class that checks if an user is an account owner. '''
    
    def has_permission(self,request,view):
        ''' Checks if therequesting user is object owner '''
       
        return request.is_payment_provider