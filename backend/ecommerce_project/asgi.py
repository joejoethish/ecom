"""
ASGI config for ecommerce_project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings.development')

django_asgi_app = get_asgi_application()

from apps.chat import routing as chat_routing
from apps.notifications import routing as notification_routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                *chat_routing.websocket_urlpatterns,
                *notification_routing.websocket_urlpatterns,
            ])
        )
    ),
})