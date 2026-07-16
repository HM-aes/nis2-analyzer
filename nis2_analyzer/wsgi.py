"""
WSGI config for nis2_analyzer project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nis2_analyzer.settings')

application = get_wsgi_application()
