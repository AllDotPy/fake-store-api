from django.urls import path
from .consumers import TransactionConsumer

websocket_urlpatterns = [
    path("ws/realtime/transaction/", TransactionConsumer.as_asgi()),
]
