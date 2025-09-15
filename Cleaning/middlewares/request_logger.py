from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"New request: {request.method} {request.url}") # replace with logger
        response = await call_next(request)
        return response

def setup_middlewares(app):
    app.add_middleware(RequestLoggerMiddleware)
