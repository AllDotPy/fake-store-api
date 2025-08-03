from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import (
    IsAuthenticated,IsAdminUser,AllowAny
)

from apps.products.serializers import (
    ProductSerializer,
)

from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

####
##      PRODUCTS VIEWSET
#####
class ProductsViewSet(ModelViewSet):
    ''' ViewSet class for Products Model. '''
    
    queryset = ProductSerializer.Meta.model.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['category','brand']
    search_fields = [
        'name','description','brand',
        'category__name','category__description',
        'category__code','category__id'
    ]
    lookup_field = 'id'
    
    def get_permissions(self):
        ''' Define a way to use permissions based on requesting user. '''
        
        # USER MUST BE AN ADMIN BEFORE REQUESTING DELETE OR UPDATE ACTION
        if self.action in ('destroy','update'):
            self.permission_classes = [IsAuthenticated,IsAdminUser]
            
        return super().get_permissions()

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def like(self, request, id=None):
        """ Custom action to like a product. """
        try:
            product = self.get_object()
            user = request.user

            if request.method == "DELETE":
                if user in product.likes.all():
                    product.likes.remove(user)
                    return Response({'detail': 'Product unliked .'}, status=status.HTTP_200_OK)
                else:
                    return Response({'detail': 'Product not liked yet.'}, status=status.HTTP_400_BAD_REQUEST)
            if request.method == "POST":
                if user not in product.likes.all():
                    product.likes.add(user)
                    return Response({'detail': 'Product liked successfully.'}, status=status.HTTP_200_OK)
                else:
                    return Response({'detail': 'Product already liked.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
