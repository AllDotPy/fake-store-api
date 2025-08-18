from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.billings.models import Transaction
from core.exceptions import UserNotFoundError


####
##      TRANSACTIONS SERIALIZER
#####
class TransactionSerializer(serializers.ModelSerializer):
    ''' Serializer class for Transaction Model. '''

    user = UserSerializer(read_only=True)
    user_id = serializers.UUIDField(write_only=True)
    
    # META CLASS
    class Meta:
        ''' Meta class for TransactionSerializer. '''

        model = Transaction
        fields = [
            'id', 'code', 
            'user', 'user_id', 'type', 
            'status', 'amount', 'payment_link', 'reference',
            'created', 'modified'
        ]
        read_only_fields = ['id', 'code', 'payment_link', 'reference', 'created', 'modified']

    def to_representation(self, instance: Transaction):
        ''' Override representation method to add custom fields. '''
        
        # GET INSTANCE REPRESENTATION FIRST
        rep = super().to_representation(instance)
        
        # ADD CUSTOM FIELDS
        rep['status_display'] = instance.get_status_display()
        rep['type_display'] = instance.get_type_display()
        
        return rep


class TransactionCreateSerializer(serializers.ModelSerializer):
    ''' Serializer for creating transactions. '''
    
    user_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'user_id', 'type', 'amount',
        ]
    
    def validate_amount(self, value):
        ''' Validate transaction amount. '''
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value
    
    def create(self, validated_data):
        ''' Create transaction with user. '''
        from apps.accounts.models import User
        
        user_id = validated_data.pop('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise UserNotFoundError(
                details="User not found"
            )
            
        validated_data['user'] = user
        validated_data['status'] = Transaction.STATUES.PENDING
        
        return super().create(validated_data)


class TransactionUpdateSerializer(serializers.ModelSerializer):
    ''' Serializer for updating transactions. '''
    
    class Meta:
        model = Transaction
        fields = ['status']
        read_only_fields = ['status']  # Status should be updated via business logic 