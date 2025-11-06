import logging
from typing import cast

import requests
from cities_light.models import City
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from weather.models import TemperatureChoices, WeatherQuery, WeatherSnapshot
from weather.types.weather_types import WeatherData

logger = logging.getLogger(__name__)


class WeatherService:
    CACHE_KEY_PREFIX = "weather"
    UNITS_MAP = {
        TemperatureChoices.CELSIUS: "metric",
        TemperatureChoices.FAHRENHEIT: "imperial",
        TemperatureChoices.KELVIN: "standard",
    }

    @staticmethod
    def _build_api_params(lat: float, lon: float, units: str) -> dict[str, str | float]:
        return {
            "lat": lat,
            "lon": lon,
            "appid": settings.WEATHER_API_KEY or "",
            "units": units,
        }

    @staticmethod
    def find_city(city_name: str) -> City | None:
        """
        Find city in cities_light database.

        Args:
            city_name: Name of the city to search for

        Returns:
            City object if found, None otherwise
        """
        city = City.objects.filter(name__iexact=city_name).first()
        if city:
            return city

        city = City.objects.filter(search_names__icontains=city_name).first()
        return city

    @classmethod
    def fetch_weather_data(
        cls, latitude: float, longitude: float, temperature_unit: str
    ) -> WeatherData | None:
        """
        Fetch weather data from OpenWeatherMap API.

        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            temperature_unit: Temperature unit (C, F, or K)

        Returns:
            Dictionary with weather data or None if request fails
        """
        try:
            base_url = settings.WEATHER_API_BASE_URL
            units = cls.UNITS_MAP.get(cast(TemperatureChoices, temperature_unit), "standard")
            params = cls._build_api_params(latitude, longitude, units)

            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not data.get("main") or not data.get("weather"):
                logger.error(f"Invalid API response format: {data}")
                return None

            main = data.get("main", {})
            wind = data.get("wind", {})
            weather = (data.get("weather") or [{}])[0]

            return {
                "temperature": main.get("temp"),
                "feels_like": main.get("feels_like"),
                "weather_description": weather.get("description", ""),
                "humidity": main.get("humidity"),
                "wind_speed": wind.get("speed"),
                "pressure": main.get("pressure"),
                "raw_response": data,
            }
        except requests.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            return None

    @classmethod
    def get_cached_snapshot(cls, city_name: str, temperature_unit: str) -> WeatherSnapshot | None:
        """
        Retrieve cached weather snapshot.

        Args:
            city_name: Name of the city
            temperature_unit: Temperature unit (C, F, or K)

        Returns:
            WeatherSnapshot if cached and valid, None otherwise
        """
        cache_key = f"{cls.CACHE_KEY_PREFIX}:{city_name.lower()}:{temperature_unit}"
        cached_snapshot_id = cache.get(cache_key)

        if cached_snapshot_id:
            try:
                return WeatherSnapshot.objects.get(id=cached_snapshot_id)
            except WeatherSnapshot.DoesNotExist:
                cache.delete(cache_key)
        return None

    @classmethod
    def create_weather_snapshot(
        cls, city: City, weather_data: WeatherData, temperature_unit: str
    ) -> WeatherSnapshot:
        """
        Create and cache a weather snapshot.

        Args:
            city: City object
            weather_data: Weather data dictionary from API
            temperature_unit: Temperature unit (C, F, or K)

        Returns:
            Created WeatherSnapshot instance
        """
        snapshot = WeatherSnapshot.objects.create(
            city_name=city.name,
            city=city,
            temperature=weather_data["temperature"],
            feels_like=weather_data.get("feels_like"),
            weather_description=weather_data["weather_description"],
            humidity=weather_data.get("humidity"),
            wind_speed=weather_data.get("wind_speed"),
            pressure=weather_data.get("pressure"),
            temperature_unit=temperature_unit,
            raw_response=weather_data.get("raw_response"),
            fetched_at=timezone.now(),
        )

        cache_key = f"{cls.CACHE_KEY_PREFIX}:{city.name.lower()}:{temperature_unit}"
        cache_ttl = getattr(settings, "WEATHER_CACHE_TTL", 300)
        cache.set(cache_key, snapshot.id, cache_ttl)

        return snapshot

    @staticmethod
    def create_query(
        snapshot: WeatherSnapshot, served_from_cache: bool, ip_address: str | None
    ) -> WeatherQuery:
        """
        Create a weather query record.

        Args:
            snapshot: WeatherSnapshot to associate with the query
            served_from_cache: Whether the data was served from cache
            ip_address: IP address of the requester

        Returns:
            Created WeatherQuery instance
        """
        return WeatherQuery.objects.create(
            weather_snapshot=snapshot,
            served_from_cache=served_from_cache,
            ip_address=ip_address,
        )

    @classmethod
    def get_weather_for_city(
        cls, city_name: str, temperature_unit: str, ip_address: str | None
    ) -> tuple[WeatherQuery | None, str | None]:
        """
        Main method to get weather for a city.

        Args:
            city_name: Name of the city
            temperature_unit: Temperature unit (C, F, or K)
            ip_address: IP address of the requester

        Returns:
            Tuple of (WeatherQuery, error_message)
            If successful, error_message is None
            If failed, WeatherQuery is None and error_message contains the error
        """
        if not (city := cls.find_city(city_name)):
            return None, f"City '{city_name}' not found in database"

        if cached_snapshot := cls.get_cached_snapshot(city.name, temperature_unit):
            query = cls.create_query(cached_snapshot, served_from_cache=True, ip_address=ip_address)
            return query, None

        if not (
            weather_data := cls.fetch_weather_data(city.latitude, city.longitude, temperature_unit)
        ):
            return None, "Failed to fetch weather data from API"

        snapshot = cls.create_weather_snapshot(city, weather_data, temperature_unit)
        query = cls.create_query(snapshot, served_from_cache=False, ip_address=ip_address)

        return query, None
