from django.db.models import Q
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import (
    IsAuthenticated,IsAdminUser,AllowAny
)

from apps.billings.serializers import (
    TransactionSerializer, WalletSerializer,
    RechargeTransactionSerializer
)
from apps.billings.permissions import (
    IsPaymentApiProvider
)

# Create your views here.

####
##      WALLET VIEWSET
#####
class WalletViewSet(ModelViewSet):
    ''' ViewSet Class for Wallet Model. '''

    queryset = WalletSerializer.Meta.model.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'

    only_owner_actions = [
        'my_wallet'
    ]

    def get_queryset(self):
        ''' Return a specific objects based on requesting user. '''

        # ADMINS CAN SEE ALL WALLETS
        if self.request.user.is_superuser:
            return self.queryset

        return self.queryset.filter(
            user=self.request.user
        )
    
    def get_permissions(self):
        ''' Define a way to use permissions according to action. '''

        # FOR ADMINS
        if self.action == 'destroy':
            self.permission_classes = [IsAuthenticated,IsAdminUser]

        # ONLY OWNER ACTIONS
        if self.action in self.only_owner_actions:
            self.permission_classes = [IsAuthenticated,]

        return super().get_permissions()
    
    @action(methods=['GET'],detail=False,url_path='mine')
    def my_wallet(self,request):
        ''' Return a requesting user wallet. '''
        
        # REQUESTING USER
        user = self.request.user
        # GET WALLET
        wallet = self.serializer_class(
            instance = user.wallet,
            context = self.get_serializer_context()
        ).data
        
        return Response(wallet)


####
##      TRANSACTIONS VIEWSET
#####
class TransactionViewSet(ModelViewSet):
    ''' ViewSet class for Transaction Model. '''

    queryset = TransactionSerializer.Meta.model.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated,]
    # filter_backends = [filters.SearchFilter]
    search_fields = [
        'code','type','amount','subject'
    ]
    lookup_field = 'id'

    def get_queryset(self):
        ''' Return a specific objects based on requesting user. '''

        # ADMINS CAN SEE ALL WALLETS
        if self.request.user.is_staff:
            return self.queryset

        return self.queryset.filter(
            Q(rechargetransaction__user = self.request.user) |
            # RENT TRANSACTION
            Q(studentrenttransaction__rent__student__id = self.request.user.id) |
            # SERVICE PAYMENT TRANSACTION
            Q(collectiontransaction__exo__student__id = self.request.user.id) |  # FOR EXERCICES
            Q(collectiontransaction__exam__student__id = self.request.user.id) # FOR EXAMS
        )

    def get_permissions(self):
        ''' Define a way to use permissions according to action. '''

        # FOR ADMINS
        if self.action in ('destroy','update','partial_update'):
            self.permission_classes = [
                IsAuthenticated,IsAdminUser
            ]

        return super().get_permissions()

    @action(methods=['GET'],detail=True)
    def get_bill_url(self,request,id):
        ''' Return payment transaction bill_url. '''

        # GET OBJECT FIRST
        obj = self.get_object()

        if obj:
            # THEN RETURN TRANSACTION OBJECT'S BILL URL
            return Response(
                {
                    'bill_url': obj.get_bill_url()
                },
                status = 200
            )
        # OBJECT NOT FOUND
        return Response(
            {
                'details':f'Transaction object with uuid "{id}" does not exist.'
            },
            status = 404
        )
        

####
##      RECHARGE TRANSACTIONS VIEWSET
#####
class RechargeTransactionViewSet(ModelViewSet):
    ''' ViewSet class for Recharge Transaction. '''
    
    queryset = RechargeTransactionSerializer.Meta.model.objects.all()
    serializer_class = RechargeTransactionSerializer
    permission_classes = [IsAuthenticated,]
    # filter_backends = [filters.SearchFilter]
    search_fields = [
        'code','type','amount'
    ]
    lookup_field = 'id'

    def get_queryset(self):
        ''' Return a specific objects based on requesting user. '''

        # ADMINS CAN SEE ALL WALLETS
        if self.request.user.is_staff:
            return self.queryset

        return self.queryset.filter(
            user = self.request.user
        )

    def get_permissions(self):
        ''' Define a way to use permissions according to action. '''

        # FOR ADMINS
        if self.action in ('destroy','update','partial_update'):
            self.permission_classes = [
                IsAuthenticated,IsAdminUser
            ]

        # FOR SEMOA VALIDATION
        if self.action == 'process':
            self.permission_classes = [
                IsPaymentApiProvider
            ]

        return super().get_permissions()
    
    @action(methods=['POST'],detail=True)
    def process(self,request,id):
        ''' Changes ransaction status when payment is processed by user. '''

        # GET TRANSACTION OBJECT FIRST
        obj = self.get_object()
        # AND SECONG GET REQUEST DATA
        state = request.data.get('success')
        # IF OBJ
        if obj:
            # THEN CHECK IF TRANSACTION IS NOT ALREADY PROCESSED
            if not obj.is_called_back:
                # THEN UPDATE TRANSACTION STATUS
                obj.is_called_back = True
                obj.succed() if state == True else obj.fail()

        # RETURN RESPONSE
        return Response(
            {
                {'OK':True}
            }
        )