from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from shared.logging.logger import Logger

my_logger = Logger.get_logger()


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        my_logger.info(f"New request: {request.method} {request.url}") 
        response = await call_next(request)
        return response

def setup_middlewares(app):
    app.add_middleware(RequestLoggerMiddleware)
