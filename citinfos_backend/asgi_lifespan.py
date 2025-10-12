"""
ASGI Lifespan handler to manage application lifecycle properly.

This prevents the "took too long to shut down and was killed" warnings
by ensuring database connections and other resources are cleaned up properly.
"""

import logging
from django.db import close_old_connections

logger = logging.getLogger(__name__)


class ASGILifespanHandler:
    """
    ASGI Lifespan handler for proper startup and shutdown.

    Wraps the main ASGI application to handle lifespan events.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            while True:
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    # Startup logic
                    logger.info("ASGI application starting up...")
                    await send({'type': 'lifespan.startup.complete'})
                elif message['type'] == 'lifespan.shutdown':
                    # Shutdown logic - close database connections
                    logger.info("ASGI application shutting down...")
                    close_old_connections()
                    await send({'type': 'lifespan.shutdown.complete'})
                    return
        else:
            # Pass through to the wrapped application
            await self.app(scope, receive, send)
