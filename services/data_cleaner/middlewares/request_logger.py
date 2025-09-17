# Playmaker/services/data_cleaner/middlewares/request_logger.py
from __future__ import annotations
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from Playmaker.shared.logging.logger import Logger

# use a specific name so it rolls up under "playmaker" and stays filterable
log = Logger.get_logger(name="playmaker.data_cleaner.http")

class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        method = request.method
        path = request.url.path
        client = getattr(request.client, "host", None)

        # entry line
        log.info(f"request start method={method} path={path} client={client}")

        try:
            response = await call_next(request)
            duration_ms = int((time.perf_counter() - start) * 1000)
            # exit line
            log.info(
                f"request end   method={method} path={path} status={response.status_code} "
                f"duration_ms={duration_ms} client={client}"
            )
            return response
        except Exception as e:
            duration_ms = int((time.perf_counter() - start) * 1000)
            # include traceback to console; ES handler will still capture message/level/name
            log.error(
                f"request error method={method} path={path} duration_ms={duration_ms} "
                f"client={client} err={e}",
                exc_info=True,
            )
            raise

def setup_middlewares(app):
    app.add_middleware(RequestLoggerMiddleware)
