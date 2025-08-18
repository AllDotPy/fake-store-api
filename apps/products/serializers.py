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

        rep = super().to_representation(
            instance=instance
        )
        return {
            'id': rep['id'],
            'code': rep['code'],
            'file': rep['file']
        }

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

        user = self.context.get('view').request.user
        
        rep['category'] = {
            'id': str(instance.category.id),
            'code': instance.category.code,
            'name': instance.category.name
        }
        # Likes
        likes = instance.likes.all()
        rep['likes'] = likes.count()
        rep['has_been_liked'] = likes.filter(id = user.id).exists()

        # Add media details using ProductMediaSerializer
        media_queryset = instance.medias.all()
        rep['medias'] = ProductMediaSerializer(
            media_queryset, many=True, context = self.context
        ).data
        
        return rep