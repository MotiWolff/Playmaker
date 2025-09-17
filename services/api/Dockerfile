# syntax=docker/dockerfile:1
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
# Install minimal runtime deps; extend as needed in requirements later
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir fastapi uvicorn
# Copy requirements and install dependencies
COPY services/api/requirements.txt /app/services/api/requirements.txt
RUN pip install --no-cache-dir -r /app/services/api/requirements.txt
# Copy only what's needed for this service
COPY shared /app/shared
COPY services/api /app/services/api
EXPOSE 8000
CMD ["sh","-c","uvicorn services.api.main:app --host 0.0.0.0 --port 8000"]
