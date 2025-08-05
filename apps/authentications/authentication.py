from rest_framework.viewsets import GenericViewSet
from rest_framework import (
    exceptions, permissions
)
from django.db.models import Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.serializers import(
    UserSerializer,
)
from apps.utils.functions import (
    get_object_or_None,send_simple_notfication
)
from core.infobip import (
    MessageManager,
)
from apps.authentications.models import (
    Otp
)
from core.exceptions import (
    UserAuthenticationError,
    UserNotFoundError,
    TokenError,
    DataValidationError,
    ServiceUnavailableError
)

# GET USER MODEL FIRST
USER = get_user_model()


####
##      USER AUTHENTICATION CLASS
#####
class AuthenticationView(GenericViewSet):
    ''' Handle authentication '''
    
    queryset = USER.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_user(self,username):
        ''' Retrieve user account '''
        
        # NOTE : USERNAME VALUE CAN BE ONLY PHONE NUMBER OR EMAIL NOT USERNAME
        
        try:
            return USER.objects.get(
                Q(email__iexact = username, is_deleted = False)|
                Q(phone_number__iexact = username, is_deleted=False)|
                Q(username__exact = username, is_deleted = False)
            )
        # USER DOES NOT EXIST OR IS NOT ACTIVE
        except USER.DoesNotExist as e:
            print(str(e))
            return None
            # raise exceptions.AuthenticationFailed(
            #     " No active user has been found with the provided credentials. "
            # ) from exceptions
    
    def generate_token(self, serialized_user):
        """ Generate User token """
        
        user = self.get_user(serialized_user.data["email"])
        refresh = RefreshToken.for_user(user)

        return {
            "user": serialized_user.data,
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }
        
    def authenticate(self, request):
        """ Authenticate User """
        
        username = request.data.get('login')
        password = request.data.get('password')

        user = None

        # VALIDATE AUTH PROVIDER
        if username not in('',' ',None):
            user = self.get_user(username)
        else:
            raise exceptions.ValidationError(
                " Login must be phone_number or Email based "
            )

        # THERE IS NO USER REGISTERED WITH PROVIDED CREDENTIALS
        if user is None:
            raise exceptions.AuthenticationFailed(
                " No active user has been found with the provided credentials "
            )

        # Validate password
        if password is not None and user.check_password(password):
            user.last_login = timezone.now()
            user.save()
            return Response(self.generate_token(self.get_serializer(user)))
        else:
            raise exceptions.AuthenticationFailed("Invalid password")
        
    def logout(self, request):
        """ Logout user by blacklisting the refresh token. """

        refresh_token = request.data.get('refresh')

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()

                return Response(
                    {"message": "Successfully logged out."},
                    status=205  # RESET CONTENT
                )
            except Exception as e:
                print(e)
                raise TokenError(
                    details="Failed to logout."
                )
        else:
            raise UserAuthenticationError(
                details="No valid refresh token provided."
            )
        
    def register(self, request):
        """ Register a new User. """
        
        serializer = self.get_serializer(data=request.data)
        
        # VALIDATE PASSWORD
        if len(request.data['password'])<8:
            raise exceptions.ValidationError(
                {"Password":"Password should have at least 8 characters."}
            )

        # VALIDATE DATA
        if serializer.is_valid(raise_exception=True):
            usr = serializer.save()
            return Response(self.generate_token(serializer))
        
    def send_otp(self,request,pk):
        ''' Send OTP verification code to user. '''
        
        # ENSURE USER WITH UUID "pk" EXISTS
        obj = get_object_or_None(
            self.serializer_class.Meta.model, 
            id = pk
        )
        
        if obj is not None:
            # CREATE OTP OBJECT FOR USER
            otp = Otp.objects.create(user = obj)
            
            # THEN SEND CODE TO USER VIA SMS
            response = send_simple_notfication(
                f'Your DREAMMORE verification code is : {otp.digits}',
                _to=str(obj.phone_number)
            )
            
            if response:
                return Response(
                    {
                        'status':'success',
                        'message':f'Verification code successfully sent.',
                        'data':{
                            'user':str(obj.id)
                        }
                    },
                    status = 200
                )
            
            # INVALID PHONE NUMBER
            raise ServiceUnavailableError(
                details="Error sending otp code."
            )
            
        # USER DOESNOT EXISTS
        raise UserNotFoundError(
            details=f'No such user exists with the uuid "{pk}".'
        )
    
    def verify_code(self,request,pk):
        ''' Verify user opt code. '''
        
        # GET THE REQUESTING CODE
        code = request.data.get('code')
        
        # ENSURE USER WITH UUID "pk" EXISTS
        obj = get_object_or_None(
            self.serializer_class.Meta.model,
            id=pk
        )
        
        if obj is not None:
            # THEN VERIFY USER CODE
            otp = obj.otps.all().first()
            
            if otp and otp.is_valid():
                
                if otp.check_otp_code(code):
                    # THEN MARK USER OBJECT AS VERIFIED
                    obj.mark_as_verified()
                    
                    # NOW WE MUST DELETE THE JUST USED OTP OBJECT
                    obj.otps.all().delete()
                    
                    #AND RETURN RESPONSE
                    return Response(
                        {
                            'status':'success',
                            'message':f'Phone number successfully verified.',
                            'data':{
                                'code':self.get_serializer(instance=obj).data
                            }
                        },
                        status=200
                    )
                    
                # CODE HAS EXPIRED
                raise UserAuthenticationError(
                    details="Invalid OTP code."
                )
                
            # CODE IS NOT VALID
            raise DataValidationError(
                details="Code has expired."
            )
            
        # USER DOESNOT EXISTS
        raise UserNotFoundError(
            details=f'No such user exists with the uuid "{pk}".'
        )
        
    def verify_email_or_phone(self,request):
        ''' Check that a given phone numbre already exists. '''
        
        # GET REQUEST DATA
        data = request.data
        
        # GET USER BY PHONE NUMBER FIRST
        obj = get_object_or_None(
            self.serializer_class.Meta.model,
            **data
        )
        
        if obj is not None:
            # THEN RETURN TRUE
            return Response(
                {
                    'exist':True
                },
                status = 400
            )
        
        else:
            # ELSE FALSE
            return Response(
                {
                    'exist':False
                },
                status = 200
            )
            
    def change_password(self,request):
        ''' Change user password. '''
        
        # GET REQUEST DATA
        data = request.data
        
        # GET REQUESTING USER
        user = request.user
        
        # USER MUST BE AUTHENTICATED
        if user.is_authenticated:
            
            # CHECK OLD PASSWORD
            if user.check_password(data['old_password']):
                # THEN CHANGE IT
                user.set_password(data['new_password'])
                user.save()
                
                return Response(
                    {
                        'status':'success',
                        'message':'password updated.'
                    },
                    status = 200
                )
                
            # WRONG PASSWORD
            raise UserAuthenticationError(
                details="Wrong password."
            )
            
        # USER IS NOT AUTHENTICATED
        raise UserAuthenticationError(
            details="You must be authenticated."
        )
        
    def check_phone_and_send_otp(self,request,phone):
        ''' Check that a user with phone_number "phone" exists and send otp to him. '''
        
        # TRYING TO GET USER OBJECT
        obj = get_object_or_None(
            self.serializer_class.Meta.model,
            phone_number = phone
        )
        
        # OBJ MUST NOT BE NONE
        if obj is not None:
            # THEN SEND OTP CODE USING "send_otp" METHOD
            obj.revok_verification()
            obj.deactivate()
            return self.send_otp(request,obj.id)
        
        # NO USER WITH PROVIDED PHONE NUMBRE FOUND
        raise UserNotFoundError(
            details=f'No user with provided phone number "{phone}" found.'
        )
        
    def renew_password(self,request,pk):
        ''' Renew a given id user's password '''
        
        # TRYING TO GET USER WITH UUID "pk"
        obj = get_object_or_None(
            self.serializer_class.Meta.model,id=pk
        )
        
        # GET PASSWORD FROM REQUEST
        password = request.data.get('password')
        
        # OBJ MUST NOT BE NONE
        if obj is not None:
            # THEN CHANGE HIS PASSWORD
            obj.set_password(password)
            obj.save()
            obj.activate()
            # NOW RETURN SUCCESS RESPONSE
            return Response(
                {
                    'status':'success',
                    'message':'password updated.'
                },
                status = 200
            )
            
        # USER NOT FOUND
        raise UserNotFoundError(
            details=f'User object with uuid "{pk}" does not exists.'
        )