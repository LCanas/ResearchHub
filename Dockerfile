# Container image for the Collaboration Hub (Flask + gunicorn).
# Works on Azure App Service (Web App for Containers), a KCL VM, or any host
# that runs containers.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Most hosts (incl. Azure App Service) provide the listening port via $PORT.
ENV PORT=8000
EXPOSE 8000

# Seed on first boot (only if the DB is empty), then serve.
CMD ["sh", "-c", "python init_db.py && gunicorn --bind=0.0.0.0:${PORT} --timeout 600 --workers 1 wsgi:app"]
