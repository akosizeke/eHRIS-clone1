"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Points WSGI servers to the main Django settings module.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# WSGI callable used by production web servers.
application = get_wsgi_application()
