"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Points ASGI servers to the main Django settings module.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# ASGI callable used when serving the project asynchronously.
application = get_asgi_application()
