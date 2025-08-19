from rest_framework import serializers
from django.db import transaction

from apps.billings.serializers import TransactionSerializer
from apps.orders.models import (
    Article, Order
)
from apps.products.serializers import (
    ProductSerializer
)
from apps.accounts.serializers import UserSerializer

####
##      ARTICLES SERIALIZER
#####
class ArticleSerializer(serializers.ModelSerializer):
    ''' Serializer class for Articles Model. '''
    
    # META CLASS
    class Meta:
        ''' Meta class for Article Serializer. '''
        model = Article
        fields = (
            "product",
            "selling_price",
            "quantity"
        )
        
    def to_representation(self, instance:Article):
        ''' Override Instance reprensentation method to customize fields. '''
        
        # GET INSTANCE REPRESENTATION FIRST
        rep = super().to_representation(instance)
        
        rep['product'] = ProductSerializer(
            instance = instance.product
        ).data
        
        rep['total'] = instance.total()
        
        return rep
    
    
####
##      ORDER SERIALIZER
#####
class OrderSerializer(serializers.ModelSerializer):
    ''' Serializer class for Orders Model. '''
    
    articles = ArticleSerializer(many = True)
    status = serializers.CharField(default=Order.OrderStatus.WAITING_FOR_PAYMENT)

    # META CLASS
    class Meta:
        ''' Meta class for Order Serializer. '''
        model = Order
        fields = (
            'id',
            'client',
            'articles',
            'total',
            'status',
            'created',
            'modified'
        )
        extra_kwargs = {
            'client':{'read_only': True},
            'total':{'read_only': True},
            # 'articles':{'read_only': True},
            'created':{'read_only': True},
            'modified':{'read_only': True},
            # 'is_paid':{'read_only': True}
        }
        
    def to_representation(self, instance:Order):
        ''' Override Instance reprensentation method to customize fields. '''
        
        # GET INSTANCE REPRESENTATION FIRST
        rep = super().to_representation(instance)
        
        # ADD CLIENT REPRESENTATION 
        rep['client'] = UserSerializer(
            instance = instance.client
        ).data
        
        # ADD ARTICLES TO REPRESENTATION
        rep['articles'] = ArticleSerializer(
            instance = instance.articles,
            many = True
        ).data
        
        # ADD TOTAL
        rep['total'] = instance.total()
        
        # ADD TRANSACTION
        transaction = instance.transactions.first()
        rep['transaction'] = TransactionSerializer(transaction).data if transaction else None
                
        return rep

    def create(self, validated_data):
        ''' Override create method to auto create articles. '''
        
        articles = validated_data.pop('articles')
        user = self.context['request'].user

        # Créer l'ordre
        order = Order.objects.create(
            **validated_data,
            client=user
        )
        
        # Créer tous les articles
        for article_data in articles:
            Article.objects.create(**article_data, order=order)
        
        if order:    
            # CREATE TRANSACTION FOR ORDER
            from apps.billings.models import Transaction
            
            order_transaction = Transaction.objects.create(
                user=order.client,
                order=order,
                type=Transaction.TYPES.PAYMENT,
                amount=float(order.total()),
            )
        
        return order