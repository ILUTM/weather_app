import pytest
import time
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings

from app.middlewares.rate_limit import RateLimitMiddleware


@pytest.mark.django_db
class TestRateLimitMiddleware:

    def make_request(self, rf, path="/api/weather/fetch/", method="post", ip="192.168.1.1"):
        req = getattr(rf, method.lower())(path)
        req.META["REMOTE_ADDR"] = ip
        return req

    def test_allows_first_request(self, middleware, rf):
        request = self.make_request(rf)
        response = middleware(request)
        assert response.status_code == 200

    def test_blocks_after_limit_exceeded(self, middleware, rf):
        ip = "1.2.3.4"
        for _ in range(settings.RATE_LIMIT_PER_MINUTE):
            response = middleware(self.make_request(rf, ip=ip))
            assert response.status_code == 200
        response = middleware(self.make_request(rf, ip=ip))
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.content.decode()

    def test_resets_after_period(self, middleware, rf, monkeypatch):
        ip = "1.2.3.4"
        now = time.time()
        for _ in range(settings.RATE_LIMIT_PER_MINUTE):
            response = middleware(self.make_request(rf, ip=ip))
            assert response.status_code == 200
        monkeypatch.setattr("time.time", lambda: now + settings.RATE_PERIOD + 1)
        response = middleware(self.make_request(rf, ip=ip))
        assert response.status_code == 200

    def test_different_ips_have_separate_limits(self, middleware, rf):
        ip1, ip2 = "1.1.1.1", "2.2.2.2"
        for _ in range(settings.RATE_LIMIT_PER_MINUTE):
            middleware(self.make_request(rf, ip=ip1))
        blocked = middleware(self.make_request(rf, ip=ip1))
        assert blocked.status_code == 429
        allowed = middleware(self.make_request(rf, ip=ip2))
        assert allowed.status_code == 200

    def test_only_applies_to_specific_endpoint(self, middleware, rf):
        request = self.make_request(rf, path="/api/other/", method="get")
        response = middleware(request)
        assert response.status_code == 200
