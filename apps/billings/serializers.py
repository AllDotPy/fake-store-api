from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.billings.models import (
    Wallet, Transaction, RechargeTransaction,
)



####
##      WALLET SERIALIZER
#####
class WalletSerializer(serializers.ModelSerializer):
    ''' Serializer class for Wallet Model. '''

    # META CLASS
    class Meta:
        ''' Meta class for WalletSerializer. '''

        model = Wallet
        fields = '__all__'

    def to_representation(self, instance):
        ''' Override representation method to add customfields. '''

        # GET INSTANCE OBJECT REPRESENTATION
        rep =  super().to_representation(instance)

        # GET RELATED USER AND ADD IT TO INSTANCE FINAL REPRESENTATION
        user = UserSerializer(
            instance=instance.user
        ).data

        rep['user'] = user

        return rep
    
    
####
##      TRANSACTIONS SERIALIZER
#####
class TransactionSerializer(serializers.ModelSerializer):
    ''' Serializer class for Transaction Model. '''

    # META CLASS
    class Meta:
        ''' Meta class for TransactionSerializer. '''

        model = Transaction
        fields = '__all__'

    def to_representation(self, instance:Transaction):
        ''' Override representation method to add custom fields. '''

        # GET INSTANCE REPRESENTATION FIRST
        rep = super().to_representation(instance)

        def get_serializer(_type):
            ''' return A serializer class to use based on transaction type. '''
            return {
                Transaction.SUBJECTS.RECHARGE: {
                    'class':RechargeTransactionSerializer,
                    'subinstance': 'rechargetransaction'
                },
                Transaction.SUBJECTS.RENT: {
                    'class':StudentRentTransactionSerializer,
                    'subinstance': 'studentrenttransaction'
                },
                Transaction.SUBJECTS.COLLECTION: {
                    'class': CollectionTransactionSerializer,
                    'subinstance': 'collectiontransaction'
                }
            }.get(_type,None)

        # GET THE RIGHT SERIALIZER FOR INSTANCE
        serializer = get_serializer(instance.subject)
        if serializer:
            # THEN RETURN SERILIZED DATA FROM SERIALIZER
            return serializer['class'](
                instance = getattr(instance,serializer['subinstance']), 
                many = False,
                context = self.context
            ).data
        
        # USE DEFAULT REPRESENTATION ELSE
        return rep
    
    
####
##      RECHARGE TRANSACTIONS SERIALIZER
#####
class RechargeTransactionSerializer(serializers.ModelSerializer):
    ''' Serializer class for RechargeTransaction Model. '''

    # META CLASS
    class Meta:
        ''' Meta class for RechargeTransactionSerializer. '''

        model = RechargeTransaction
        fields = '__all__'
        extra_kwargs = {
            'user':{
                'read_only':True,
            },
            'provider':{
                'read_only':True
            }
        }

    def create(self,validated_data):
        ''' Override create method to add requesting user to the object. '''

        obj = self.Meta.model.objects.create(
            **validated_data,
            # provider = get_default_aggregator(),
            user = self.context.get('request').user
        )

        return obj

    def to_representation(self,instance:RechargeTransaction):
        ''' Override representation method to customize fields. '''

        # FIRST GET INSTANCE REPRESENTATION
        rep = super().to_representation(instance)

        # AMOUNT FORMAT
        rep['amount'] = int(instance.amount)

        # THEN REPLACE USER FIELD VALUE WITH SERIALIZED USER DATA
        # NOTE THAT WE NEED TO DO THIS ONLY IF REQUESTING USER IS STAFF OR SUPERUSER
        if self.context.get('request').user.is_staff:
            # THEN ADD USER REPRESENTATION TO FINAL REPRESENTATION
            rep['user'] = UserSerializer(
                instance = instance.user
            ).data

        # NOW RETURN FINAL REPRESENTATION
        return rep
