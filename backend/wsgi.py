"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
import sys

from django.core.wsgi import get_wsgi_application

# Default settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Optional automatic migrations on startup. Set the environment variable
# `AUTO_MIGRATE=true` in your production environment (Render) if you want
# the app to attempt to run `manage.py migrate` before serving requests.
if os.environ.get('AUTO_MIGRATE', '').lower() in ('1', 'true', 'yes'):
	try:
		# Import and configure Django, then run migrations programmatically.
		import django
		from django.core.management import call_command

		django.setup()
		# Run migrations non-interactively. Failures are printed but won't
		# prevent the WSGI app from starting (so the process still comes up).
		call_command('migrate', '--noinput')
	except Exception as exc:
		print(f"[wsgi] AUTO_MIGRATE failed: {exc}", file=sys.stderr)

application = get_wsgi_application()
