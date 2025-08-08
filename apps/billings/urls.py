from rest_framework import routers

from apps.billings.views import (
    TransactionViewSet,
)


# INSTANCIATE DEFAULT ROUTER
router = routers.DefaultRouter(trailing_slash = False)

# TRANSACTIONS URLS
router.register(
    'transactions', TransactionViewSet
)

urlpatterns = router.urls