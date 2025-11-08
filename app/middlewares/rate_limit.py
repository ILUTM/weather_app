import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status

from common.get_client_ip import get_client_ip


class RateLimitMiddleware:
    CACHE_KEY_PREFIX = "rate_limit"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/api/weather/fetch/" and request.method == "POST":
            ip_address = get_client_ip(request)

            if not self._check_rate_limit(ip_address):
                return JsonResponse(
                    {
                        "error": "Rate limit exceeded. Please try again later.",
                        "detail": f"Maximum {settings.RATE_LIMIT_PER_MINUTE}"
                        "requests per minute allowed.",
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

        response = self.get_response(request)
        return response

    def _check_rate_limit(self, ip_address: str) -> bool:
        """
        Check if IP address is within rate limit.

        Returns:
            True if within limit, False if limit exceeded
        """
        cache_key = f"{self.CACHE_KEY_PREFIX}:{ip_address}"

        request_data = cache.get(cache_key)
        current_time = time.time()

        if request_data is None:
            cache.set(cache_key, {"count": 1, "start_time": current_time}, settings.RATE_PERIOD)
            return True

        time_passed = current_time - request_data["start_time"]

        if time_passed > settings.RATE_PERIOD:
            cache.set(cache_key, {"count": 1, "start_time": current_time}, settings.RATE_PERIOD)
            return True

        if request_data["count"] >= settings.RATE_LIMIT_PER_MINUTE:
            return False

        request_data["count"] += 1
        remaining_time = settings.RATE_PERIOD - time_passed
        cache.set(cache_key, request_data, int(remaining_time) + 1)

        return True
