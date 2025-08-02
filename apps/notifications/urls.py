from rest_framework import routers

from apps.notifications.views import (
    NotificationServiceViewSet,
    ReminderSettingViewSet,
    NotificationViewSet
)


# INSTANCIATE DEFAULT ROUTER
router = routers.DefaultRouter(trailing_slash = False)

# NOTIFICATIONS URLS
router.register(
    'notifs', NotificationViewSet
)

# NOTIFICATIONS SERVICES URLS
router.register(
    'services', NotificationServiceViewSet
)

# NOTIFICATIONS REMINDERS SERVICES URLS
router.register(
    'reminders', ReminderSettingViewSet
)

urlpatterns = router.urls