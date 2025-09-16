"""
Enhanced middleware module for logging HTTP requests in FastAPI.

This module:
    - Logs HTTP method, URL, client IP, and response time for each request.
    - Generates a unique request ID for tracking.
    - Provides a helper function `setup_middlewares` to attach the middleware to a FastAPI app.
"""

import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from shared.logging.logger import Logger

my_logger = Logger.get_logger()


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs details of each incoming HTTP request including:
        - HTTP method and URL
        - Client IP address
        - Response time
        - Unique request ID
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process an incoming request, log relevant details, and call the next middleware or endpoint.

        Args:
            request (Request): The incoming FastAPI request object.
            call_next (Callable): Function to call the next middleware or endpoint.

        Returns:
            Response: The response from the next middleware or endpoint.
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())
        client_ip = request.client.host if request.client else "unknown"

        # Add request ID to request state for downstream usage if needed
        request.state.request_id = request_id

        my_logger.info(f"New request: {request.method} {request.url} | "
                       f"\nClient IP: {client_ip} | \nRequest ID: {request_id} |")

        response = await call_next(request)

        process_time_ms = (time.time() - start_time) * 1000
        my_logger.info(f"Completed request: {request.method} {request.url} | "
                       f"Request ID: {request_id} | Response time: {process_time_ms:.2f}ms")

        # Optionally, attach the request ID to the response headers
        response.headers["X-Request-ID"] = request_id

        return response


def setup_middlewares(app):
    """
    Attach all middlewares to the FastAPI app.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    app.add_middleware(RequestLoggerMiddleware)
