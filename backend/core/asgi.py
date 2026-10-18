"""ASGI config: HTTP (Django) + WebSocket (Channels)."""
import os
from urllib.parse import urlparse

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# باید قبل از import کردن روت‌های چت اجرا شود
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import OriginValidator  # noqa: E402
from django.conf import settings  # noqa: E402

import chat.routing  # noqa: E402

# دامنه‌هایی که اجازه اتصال WebSocket دارند (همان CORS_ALLOWED_ORIGINS)
if settings.DEBUG:
    allowed_origins = ["*"]
else:
    allowed_origins = [
        urlparse(o).hostname
        for o in settings.CORS_ALLOWED_ORIGINS
        if urlparse(o).hostname
    ]

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": OriginValidator(
            URLRouter(chat.routing.websocket_urlpatterns),
            allowed_origins,
        ),
    }
)
