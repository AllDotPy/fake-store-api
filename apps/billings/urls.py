from rest_framework import routers

from apps.billings.views import (
    TransactionViewSet,
)


# INSTANCIATE DEFAULT ROUTER
router = routers.DefaultRouter(trailing_slash = False)

# BILLINGS URLS
router.register(
    '', TransactionViewSet
)

urlpatterns = router.urls