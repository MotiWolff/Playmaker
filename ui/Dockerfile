# syntax=docker/dockerfile:1
FROM node:18-alpine
WORKDIR /app
COPY ui/package*.json ./
RUN npm ci --ignore-scripts
COPY ui .
EXPOSE 5173
CMD ["npm","run","dev","--","--host","0.0.0.0","--port","5173"]
