import pytest
from django.core.cache import cache
from django.http import JsonResponse

from app.middlewares.rate_limit import RateLimitMiddleware


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def get_response():
    return lambda request: JsonResponse({"ok": True})


@pytest.fixture
def middleware(get_response):
    return RateLimitMiddleware(get_response)
