"""
ASGI config for server project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from apps.realtime.routing import websocket_urlpatterns
from apps.realtime.ws_auth import JwtOrSessionAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtOrSessionAuthMiddleware(
        # AuthMiddlewareStack manage sessions and cookies
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
