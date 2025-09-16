# syntax=docker/dockerfile:1
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir -U pip
COPY services/model/requirements.txt /app/services/model/requirements.txt
RUN pip install --no-cache-dir -r /app/services/model/requirements.txt
COPY shared /app/shared
COPY services/model /app/services/model
EXPOSE 8080
CMD ["python","-m","services.model.main","serve"]


