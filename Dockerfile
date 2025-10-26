# Lightweight Dockerfile for running the Flask app on Render or any container platform
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# system deps (if any) - keep minimal
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Render provides a PORT environment variable; fall back to 5000 locally
ENV PORT 5000
EXPOSE ${PORT}

# Use gunicorn (WSGI) for production. App entrypoint is `app:app` (app.py -> create_app())
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:${PORT}", "--workers", "3"]
