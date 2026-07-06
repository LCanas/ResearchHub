"""WSGI entry point for production servers.

Azure App Service (and gunicorn generally) import the ``app`` object from here:

    gunicorn --bind=0.0.0.0 --timeout 600 wsgi:app
"""
from hub import create_app

app = create_app()
