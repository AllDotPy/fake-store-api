from rest_framework import routers

from apps.orders.views import (
    OrderViewSet,
)

# INSTANCIATE DEFAULT ROUTER
router = routers.DefaultRouter(trailing_slash = False)

# BILLS URLS
router.register(
    '', OrderViewSet
)

urlpatterns = router.urls