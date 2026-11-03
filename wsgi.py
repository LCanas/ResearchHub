"""WSGI entry point for production servers.

Azure App Service (and gunicorn generally) import the ``app`` object from here:

    gunicorn --bind=0.0.0.0 --timeout 600 wsgi:app
"""
from hub import create_app

app = create_app()

# Send newsletter issues scheduled from the admin page when their time comes.
from hub.newsletter import start_scheduler  # noqa: E402

start_scheduler(app)
