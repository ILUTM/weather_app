import logging

import requests
from django.conf import settings
from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


class WeatherAPIHealthCheck(BaseHealthCheckBackend):
    critical_service = False

    def check_status(self) -> None:
        try:
            params = {
                "q": "New York",
                "appid": settings.WEATHER_API_KEY,
            }

            response = requests.get(
                settings.WEATHER_API_BASE_URL,
                params=params,
                timeout=3,
            )
            response.raise_for_status()
            logger.info("Weather API health check passed")
        except requests.RequestException as e:
            logger.error(f"Weather API health check failed: {e}")
            raise ServiceUnavailable(f"Weather API unreachable: {str(e)}") from e

    def identifier(self) -> str:
        return "weather_api"
