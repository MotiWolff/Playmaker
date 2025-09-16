# syntax=docker/dockerfile:1
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir -U pip
COPY services/data_cleaner/requirements.txt /app/services/data_cleaner/requirements.txt
RUN pip install --no-cache-dir -r /app/services/data_cleaner/requirements.txt
COPY shared /app/shared
COPY services/data_cleaner /app/services/data_cleaner
CMD ["python","-m","services.data_cleaner"]
