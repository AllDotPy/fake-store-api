from django.db.models import Q, models
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import (
    IsAuthenticated, IsAdminUser
)
from rest_framework import status

from apps.billings.serializers import (
    TransactionSerializer,
    TransactionCreateSerializer,
    TransactionUpdateSerializer
)
from apps.billings.permissions import IsPaymentApiProvider
from apps.billings.services import PaymentService
from apps.billings.models import Transaction
from core.exceptions import (
    PaymentValidationError,
    PaymentProcessingError,
    PaymentRefundError,
    TransactionNotFoundError
)

# Create your views here.

####
##      TRANSACTIONS VIEWSET
#####
class TransactionViewSet(ModelViewSet):
    ''' ViewSet class for Transaction Model. '''

    queryset = TransactionSerializer.Meta.model.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated,]
    search_fields = [
        'code', 'type', 'amount', 'subject', 'description'
    ]
    lookup_field = 'id'

    def get_queryset(self):
        ''' Return specific objects based on requesting user. '''

        # ADMINS CAN SEE ALL TRANSACTIONS
        if self.request.user.is_staff:
            return self.queryset

        # USERS CAN ONLY SEE THEIR OWN TRANSACTIONS
        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        ''' Return appropriate serializer based on action. '''
        
        if self.action == 'create':
            return TransactionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TransactionUpdateSerializer
        return TransactionSerializer

    def get_permissions(self):
        ''' Define permissions according to action. '''

        # FOR ADMINS ONLY
        if self.action in ('destroy', 'update', 'partial_update'):
            self.permission_classes = [
                IsAuthenticated, IsAdminUser
            ]

        # FOR PAYMENT PROVIDER CALLBACKS
        if self.action in ['callback', 'verify']:
            self.permission_classes = [IsPaymentApiProvider]

        return super().get_permissions()

    @action(methods=['GET'], detail=True)
    def get_bill_url(self, request, id):
        ''' Return payment transaction bill_url. '''

        # GET OBJECT FIRST
        obj = self.get_object()

        if obj and obj.bill_url:
            # THEN RETURN TRANSACTION OBJECT'S BILL URL
            return Response(
                {
                    'bill_url': obj.get_bill_url()
                },
                status=200
            )
        
        # OBJECT NOT FOUND OR NO BILL URL
        return Response(
            {
                'detail': f'Transaction with id "{id}" does not exist or has no bill URL.'
            },
            status=404
        )

    @action(methods=['POST'], detail=True)
    def callback(self, request, id):
        ''' Handle payment provider callback. '''

        # GET TRANSACTION OBJECT FIRST
        obj = self.get_object()
        
        # GET REQUEST DATA
        success = request.data.get('success', False)
        transaction_id = request.data.get('transaction_id')
        
        if obj:
            # UPDATE TRANSACTION STATUS
            if success:
                obj.succeed()
            else:
                obj.fail()
                
            # UPDATE PROVIDER REFERENCE IF PROVIDED
            if transaction_id:
                obj.set_provider_reference(transaction_id)

        # RETURN RESPONSE
        return Response(
            {'status': 'OK'},
            status=200
        )

    @action(methods=['GET'], detail=True)
    def verify(self, request, id):
        ''' Verify transaction status with provider. '''

        # GET OBJECT FIRST
        obj = self.get_object()
        
        if obj:
            try:
                # VERIFY WITH PROVIDER
                response = PaymentService().verify_transaction(obj)
                
                if not response.has_error:
                    # UPDATE TRANSACTION STATUS BASED ON PROVIDER RESPONSE
                    provider_status = response.json.get('status', '')
                    
                    if provider_status == 'SUCCESS':
                        obj.succeed()
                    elif provider_status == 'FAILED':
                        obj.fail()
                    
                    return Response(
                        {
                            'status': 'verified',
                            'provider_status': provider_status,
                            'transaction_status': obj.status
                        },
                        status=200
                    )
                else:
                    return Response(
                        {
                            'detail': 'Failed to verify transaction with provider'
                        },
                        status=400
                    )
                    
            except PaymentValidationError as e:
                return Response(
                    {
                        'detail': str(e)
                    },
                    status=400
                )
            except PaymentProcessingError as e:
                return Response(
                    {
                        'detail': str(e)
                    },
                    status=500
                )
            except Exception as e:
                return Response(
                    {
                        'detail': f'Error verifying transaction: {str(e)}'
                    },
                    status=500
                )
        
        return Response(
            {
                'detail': f'Transaction with id "{id}" does not exist.'
            },
            status=404
        )

    @action(methods=['POST'], detail=True)
    def refund(self, request, id):
        ''' Refund a transaction. '''

        # GET OBJECT FIRST
        obj = self.get_object()
        
        if obj and obj.can_refund():
            try:
                # REFUND TRANSACTION
                response = PaymentService().refund_transaction(obj)
                
                if not response.has_error:
                    obj.status = Transaction.STATUES.REFOUNDED
                    obj.save()
                    
                    return Response(
                        {
                            'status': 'refunded',
                            'message': 'Transaction refunded successfully',
                            'refund_id': response.json.get('refund_id')
                        },
                        status=200
                    )
                else:
                    return Response(
                        {
                            'detail': 'Failed to refund transaction'
                        },
                        status=400
                    )
                    
            except PaymentValidationError as e:
                return Response(
                    {
                        'detail': str(e)
                    },
                    status=400
                )
            except PaymentRefundError as e:
                return Response(
                    {
                        'detail': str(e)
                    },
                    status=400
                )
            except Exception as e:
                return Response(
                    {
                        'detail': f'Error refunding transaction: {str(e)}'
                    },
                    status=500
                )
        
        return Response(
            {
                'detail': 'Transaction cannot be refunded'
            },
            status=400
        )

    @action(methods=['GET'], detail=False)
    def payment_summary(self, request):
        ''' Get payment summary for user. '''
        
        user_transactions = self.get_queryset()
        
        summary = {
            'total_transactions': user_transactions.count(),
            'total_paid': user_transactions.filter(status=Transaction.STATUES.SUCCESS).count(),
            'total_pending': user_transactions.filter(status=Transaction.STATUES.PENDING).count(),
            'total_failed': user_transactions.filter(status=Transaction.STATUES.FAILURE).count(),
            'total_amount': float(user_transactions.filter(status=Transaction.STATUES.SUCCESS).aggregate(
                total=models.Sum('amount')
            )['total'] or 0)
        }
        
        return Response(summary, status=200)