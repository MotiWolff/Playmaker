# syntax=docker/dockerfile:1
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir fastapi uvicorn[standard] psycopg2-binary
COPY shared /app/shared
COPY services/model /app/services/model
EXPOSE 8080
CMD ["python","-m","services.model.main","serve"]


