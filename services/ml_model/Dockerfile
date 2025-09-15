# syntax=docker/dockerfile:1
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir -U pip
COPY shared /app/shared
COPY services/ml_model /app/services/ml_model
CMD ["python","-m","services.ml_model"]
