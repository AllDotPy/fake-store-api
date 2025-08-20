# realtime/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TransactionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

        if not (user and user.is_authenticated):
            await self.close(code=4401)  # Unauthorized
            return

        # group for authenticated user
        self.group_name = f"user_{user.id}"

        # Add user to group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        await self.close()

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)
            await self.send_json({"type": "echo", "payload": data})

    async def transaction_update(self, event):
        payload = event["payload"]
        
        await self.send(text_data=json.dumps({
            "event_type": "transaction_update",
            "payload": payload
        }))

    async def send_json(self, payload: dict):
        await self.send(text_data=json.dumps(payload))
