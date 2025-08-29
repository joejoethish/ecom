"""
WebSocket routing for the debugging app.

This module defines WebSocket URL patterns for real-time debugging dashboard
and workflow trace updates.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Dashboard real-time updates
    re_path(r'ws/debugging/dashboard/$', consumers.DashboardConsumer.as_asgi()),
    
    # Workflow trace real-time updates
    re_path(r'ws/debugging/workflow/(?P<correlation_id>[0-9a-f-]+)/$', consumers.WorkflowTraceConsumer.as_asgi()),
]