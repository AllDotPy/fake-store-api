from django.contrib.auth import get_user_model
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from urllib.parse import parse_qs
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

User = get_user_model()

class JwtOrSessionAuthMiddleware(BaseMiddleware):
    """
    - JWT: with ?token=... or Sec-WebSocket-Protocol: "Bearer,<token>"
    - else: session user 
    """

    async def __call__(self, scope, receive, send):
        # already authenticated via session?
        user = scope.get("user", None)
        if user and user.is_authenticated:
            return await super().__call__(scope, receive, send)

        # parse token from query_string
        query = parse_qs(scope.get("query_string", b"").decode())
        token = query.get("token", [None])[0]

        # or from subprotocol (Sec-WebSocket-Protocol: "Bearer,<token>")
        if not token:
            subprotocols = scope.get("subprotocols") or []
            for sp in subprotocols:
                # ex: "Bearer,<token>"
                if sp.startswith("Bearer,"):
                    token = sp.split(",", 1)[1].strip()
                    break

        # or from headers
        if not token:
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b'authorization')
            if auth_header:
                val = auth_header.decode()
                if val.lower().startswith("bearer "):
                    token = val.split(" ", 1)[1]

        if token:
            try:
                auth = JWTAuthentication()
                validated = auth.get_validated_token(token)
                user = await _get_user_from_token(auth, validated)
                scope["user"] = user
            except InvalidToken:
                await send({
                    "type": "websocket.accept"
                })
                await send({
                    "type": "websocket.close",
                    "code": 4001  # custom code
                })
                raise DenyConnection("Invalid or expired token")
        else:
            raise DenyConnection("Token missing")

        return await super().__call__(scope, receive, send)

@database_sync_to_async
def _get_user_from_token(auth: JWTAuthentication, validated_token):
    return auth.get_user(validated_token)
