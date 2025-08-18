from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import (
    IsAuthenticated,IsAdminUser,AllowAny
)

from apps.products.serializers import (
    ProductSerializer,
    ProductMediaSerializer,
)

from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status
from core.exceptions import (
    DataValidationError,
    BusinessLogicError
)

####
##      PRODUCTS VIEWSET
#####
class ProductsViewSet(ModelViewSet):
    ''' ViewSet class for Products Model. '''
    
    queryset = ProductSerializer.Meta.model.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
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

        # USER MUST BE LOGGED IN TO PERFORM LIKES
        # if self.action == 'like':
        #     self.permission_classes = [IsAuthenticated]
            
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
                    return Response(
                        self.get_serializer(product).data, 
                        status=status.HTTP_200_OK
                    )
                else:
                    raise DataValidationError(
                        details="Product not liked yet."
                    )
            if request.method == "POST":
                if user not in product.likes.all():
                    product.likes.add(user)
                    return Response(
                        self.get_serializer(product).data, 
                        status=status.HTTP_200_OK
                    )
                else:
                    raise DataValidationError(
                        details="Product already liked."
                    )
        except Exception as e:
            raise BusinessLogicError(
                details=str(e)
            )


####
##      PRODUCTMEDIAS VIEWSET
#####
class ProductMediasViewSet(ModelViewSet):
    """ ViewSet class for ProductMedia Model. """

    queryset = ProductMediaSerializer.Meta.model.objects.all()
    serializer_class = ProductMediaSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['title', 'product']
    search_fields = [
        'title', 'product__name',
    ]
    lookup_field = 'id'

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.kwargs.get('product_id')  # From nested URL
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset

    def get_permissions(self):
        """ Define a way to use permissions based on requesting user. """

        # USER MUST BE AN ADMIN BEFORE REQUESTING DELETE OR UPDATE ACTION
        if self.action in ('destroy', 'update'):
            self.permission_classes = [IsAuthenticated, IsAdminUser]

        return super().get_permissions()