from rest_framework import routers

from apps.products.views import (
    ProductsViewSet,
    ProductMediasViewSet,
)

# INSTANCIATE DEFAULT ROUTER
router = routers.DefaultRouter(trailing_slash = False)

# PRODUCTS URLS
router.register(
    '', ProductsViewSet
)
router.register(
    r'(?P<product_id>[^/.]+)/medias', ProductMediasViewSet
)

urlpatterns = router.urls