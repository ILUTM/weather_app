import json
import logging
import time
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("request_logger")


class LoggingMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start_time: float = time.monotonic()

        logger.info(json.dumps({
            "event": "request_start",
            "method": request.method,
            "path": request.path,
        }))

        try:
            response: HttpResponse = self.get_response(request)
        except Exception as exc:
            duration: float = round((time.monotonic() - start_time) * 1000, 2)
            logger.error(json.dumps({
                "event": "error",
                "method": request.method,
                "path": request.path,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "duration_ms": duration,
            }))
            raise

        duration = round((time.monotonic() - start_time) * 1000, 2)
        logger.info(json.dumps({
            "event": "request_end",
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": duration,
        }))

        return response
