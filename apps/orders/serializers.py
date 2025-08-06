from rest_framework import serializers

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
        fields ="__all__"
        
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
    
    # META CLASS
    class Meta:
        ''' Meta class for Order Serializer. '''
        model = Order
        fields ="__all__"
        extra_kwargs = {
            'client':{
                'read_only': True
            },
            'articles':{
                'read_only': True
            }
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
        
        # ADD TOTAL TOO
        rep['total'] = instance.total()
        
        return rep
    
    def create(self, validated_data):
        ''' Override create method to auto create articles. '''
        
        # GET ARTICLES FIRST
        
        articles = validated_data.pop('articles')
        user = self.context.get('view').request.user
        # THEN CREATE THE ORDER OBJECT
        bill= Order.objects.create(
            **validated_data,
            client = user
        )
        
        # NOW ADD EACH CREATED ARTICLE TO THE ORDER
        for article in articles :
            a = Article.objects.create(**article)
            bill.articles.add(a)

        return bill