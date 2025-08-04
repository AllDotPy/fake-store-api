from rest_framework import routers

from apps.billings.views import (
    TransactionViewSet, WalletViewSet,
    RechargeTransactionViewSet
)


# INSTANCIATE DEFAULT ROUTER
router = routers.DefaultRouter(trailing_slash = False)

# TRANSACTIONS URLS
router.register(
    'transactions', TransactionViewSet
)

# RECHARGES TRANSACTIONS URLS
router.register(
    'recharges', RechargeTransactionViewSet
)

# WALLETS URLS
router.register(
    'wallets', WalletViewSet
)

urlpatterns = router.urls