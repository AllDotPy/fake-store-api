from rest_framework import serializers

from apps.products.models import (
    Product, ProductMedia,
)

####
##      PRODUCTMEDIA SERIALIZER
#####
class ProductMediaSerializer(serializers.ModelSerializer):
    """ Serializer class for ProductMedia Model. """

    # META CLASS
    class Meta:
        """ Meta class for ProductMedia Serializer. """
        model = ProductMedia
        fields = "__all__"

    def to_representation(self, instance:ProductMedia):
        """ Define how to represent ProductMedia Model Object as Json. """

        return super().to_representation(
            instance=instance
        )

####
##      PRODUCT SERIALIZER
#####
class ProductSerializer(serializers.ModelSerializer):
    ''' Serializer class for Products Model. '''
    
    # META CLASS
    class Meta:
        ''' Meta class for Product Serializer. '''
        model = Product
        fields ="__all__"
        
    def to_representation(self, instance:Product):
        ''' Override Instance reprensentation method to customize fields. '''
        
        # GET INSTANCE REPRESENTATION FIRST
        rep = super().to_representation(instance)
        
        rep['category'] = {
            'id': str(instance.category.id),
            'code': instance.category.code,
            'name': instance.category.name
        }
        # Add media details using ProductMediaSerializer
        media_queryset = instance.medias.all()
        rep['medias'] = ProductMediaSerializer(media_queryset, many=True).data
        
        return rep