from typing import cast

from rest_framework.request import Request


def get_client_ip(request: Request) -> str | None:
    """Extract client IP address from request."""
    x_forwarded_for = cast(str | None, request.META.get("HTTP_X_FORWARDED_FOR"))
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return cast(str | None, request.META.get("REMOTE_ADDR"))
