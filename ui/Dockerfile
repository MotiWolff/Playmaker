# Use nginx to serve static files
FROM nginx:alpine

# Install envsubst (gettext package)
RUN apk add --no-cache gettext

# Copy the UI files to nginx html directory
COPY . /usr/share/nginx/html/

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create startup script
RUN echo '#!/bin/sh' > /docker-entrypoint.sh && \
    echo 'export API_BASE_URL=${API_BASE_URL:-http://localhost:8000}' >> /docker-entrypoint.sh && \
    echo 'envsubst "\$API_BASE_URL" < /usr/share/nginx/html/js/api.js.template > /usr/share/nginx/html/js/api.js' >> /docker-entrypoint.sh && \
    echo 'nginx -g "daemon off;"' >> /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Create template from api.js
RUN mv /usr/share/nginx/html/js/api.js /usr/share/nginx/html/js/api.js.template

# Expose port 80
EXPOSE 80

# Start with our custom script
CMD ["/docker-entrypoint.sh"]
