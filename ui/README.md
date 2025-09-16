# Playmaker UI - Dockerized

This directory contains the dockerized vanilla JavaScript UI for the Playmaker football analytics application.

## Features

- **Nginx-based serving** for optimal performance
- **Environment variable configuration** for API endpoint
- **Health check endpoint** at `/health`
- **Gzip compression** enabled
- **Static asset caching** configured
- **SPA routing support** (serves index.html for all routes)

## Building the Docker Image

```bash
# From the ui directory
docker build -t playmaker-ui .
```

## Running Standalone

```bash
# Run the UI container
docker run -d \
  --name playmaker-ui \
  -p 5173:80 \
  -e API_BASE_URL=http://localhost:8000 \
  playmaker-ui
```

The UI will be available at: `http://localhost:5173`

## Running with Docker Compose

```bash
# From the shared directory
docker compose up ui
```

This will start the UI along with its dependencies (API, database, etc.)

## Environment Variables

- `API_BASE_URL`: Base URL for the API service (default: `http://localhost:8000`)

## Health Check

The container exposes a health check endpoint at `/health` that returns "healthy" when the service is running.

## File Structure

- `Dockerfile`: Container definition
- `nginx.conf`: Nginx configuration with optimizations
- `.dockerignore`: Files to exclude from Docker build context
- `js/api.js`: API client (uses environment variable substitution)
- `assets/`: Static assets (CSS, favicon, etc.)
- `index.html`: Main application entry point

## Development Notes

The `api.js` file uses environment variable substitution at container startup. The actual API URL is injected based on the `API_BASE_URL` environment variable.