from unittest.mock import Mock, patch

import pytest
import requests
from django.core.cache import cache

from weather.models import TemperatureChoices
from weather.services.weather_service import WeatherService


class TestFindCity:
    def test_find_city_exact_match(self, sample_city):
        result = WeatherService.find_city("Testopolis")

        assert result is not None
        assert result.name == "Testopolis"
        assert result.id == sample_city.id

    def test_find_city_case_insensitive(self, sample_city):
        result = WeatherService.find_city("TestopolIS")

        assert result is not None
        assert result.name == "Testopolis"

    def test_find_city_by_search_names(self, sample_city):
        result = WeatherService.find_city("topo")

        assert result is not None
        assert result.name == "Testopolis"

    def test_find_city_not_found(self, db):
        result = WeatherService.find_city("Nonexistent City")

        assert result is None


class TestFetchWeatherData:
    @patch("weather.services.weather_service.requests.get")
    def test_fetch_weather_data_success_celsius(self, mock_get, mock_weather_api_response):
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = WeatherService.fetch_weather_data(
            latitude=37.7749, longitude=-122.4194, temperature_unit=TemperatureChoices.CELSIUS
        )

        assert result is not None
        assert result["temperature"] == 72.5
        assert result["feels_like"] == 71.2
        assert result["weather_description"] == "clear sky"
        assert result["humidity"] == 65
        assert result["wind_speed"] == 8.5
        assert result["pressure"] == 1013
        assert result["raw_response"] == mock_weather_api_response

        mock_get.assert_called_once()
        call_args = mock_get.call_args

        assert call_args.kwargs["params"]["lat"] == 37.7749
        assert call_args.kwargs["params"]["lon"] == -122.4194
        assert call_args.kwargs["params"]["units"] == "metric"
        assert call_args.kwargs["timeout"] == 10

    @pytest.mark.parametrize(
        "temperature_unit,expected_units",
        [
            (TemperatureChoices.CELSIUS, "metric"),
            (TemperatureChoices.FAHRENHEIT, "imperial"),
            (TemperatureChoices.KELVIN, "standard"),
        ],
    )
    @patch("weather.services.weather_service.requests.get")
    def test_fetch_weather_data_different_units(
        self, mock_get, mock_weather_api_response, temperature_unit, expected_units
    ):
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = WeatherService.fetch_weather_data(
            latitude=37.7749, longitude=-122.4194, temperature_unit=temperature_unit
        )

        assert result is not None

        call_args = mock_get.call_args
        assert call_args.kwargs["params"]["units"] == expected_units

    @patch("weather.services.weather_service.requests.get")
    def test_fetch_weather_data_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException("Network error")

        result = WeatherService.fetch_weather_data(
            latitude=37.7749, longitude=-122.4194, temperature_unit=TemperatureChoices.CELSIUS
        )

        assert result is None

    @patch("weather.services.weather_service.requests.get")
    def test_fetch_weather_data_invalid_response(self, mock_get, mock_incomplete_api_response):
        mock_response = Mock()
        mock_response.json.return_value = mock_incomplete_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = WeatherService.fetch_weather_data(
            latitude=37.7749, longitude=-122.4194, temperature_unit=TemperatureChoices.CELSIUS
        )

        assert result is None

    @patch("weather.services.weather_service.requests.get")
    def test_fetch_weather_data_http_error(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        result = WeatherService.fetch_weather_data(
            latitude=37.7749, longitude=-122.4194, temperature_unit=TemperatureChoices.CELSIUS
        )

        assert result is None


class TestCacheOperations:
    def test_get_cached_snapshot_not_cached(self, db):
        cache.clear()
        result = WeatherService.get_cached_snapshot(
            city_name="Testopolis", temperature_unit=TemperatureChoices.CELSIUS
        )

        assert result is None

    def test_get_cached_snapshot_exists(self, sample_city, mock_weather_api_response):
        cache.clear()

        weather_data = {
            "temperature": 72.5,
            "feels_like": 71.2,
            "weather_description": "clear sky",
            "humidity": 65,
            "wind_speed": 8.5,
            "pressure": 1013,
            "raw_response": mock_weather_api_response,
        }

        snapshot = WeatherService.create_weather_snapshot(
            city=sample_city, weather_data=weather_data, temperature_unit=TemperatureChoices.CELSIUS
        )

        cached_snapshot = WeatherService.get_cached_snapshot(
            city_name=sample_city.name, temperature_unit=TemperatureChoices.CELSIUS
        )

        assert cached_snapshot is not None
        assert cached_snapshot.id == snapshot.id
        assert cached_snapshot.temperature == 72.5

    def test_get_cached_snapshot_expired(self, sample_city, mock_weather_api_response):
        cache.clear()
        cache_key = (
            f"{WeatherService.CACHE_KEY_PREFIX}:"
            f"{sample_city.name.lower()}:"
            f"{TemperatureChoices.CELSIUS}"
        )
        cache.delete(cache_key)

        cached_snapshot = WeatherService.get_cached_snapshot(
            city_name=sample_city.name, temperature_unit=TemperatureChoices.CELSIUS
        )

        assert cached_snapshot is None

    def test_create_weather_snapshot(self, sample_city, mock_weather_api_response):
        weather_data = {
            "temperature": 72.5,
            "feels_like": 71.2,
            "weather_description": "clear sky",
            "humidity": 65,
            "wind_speed": 8.5,
            "pressure": 1013,
            "raw_response": mock_weather_api_response,
        }

        snapshot = WeatherService.create_weather_snapshot(
            city=sample_city, weather_data=weather_data, temperature_unit=TemperatureChoices.CELSIUS
        )

        assert snapshot.id is not None
        assert snapshot.city_name == "Testopolis"
        assert snapshot.city == sample_city
        assert snapshot.temperature == 72.5
        assert snapshot.feels_like == 71.2
        assert snapshot.weather_description == "clear sky"
        assert snapshot.humidity == 65
        assert snapshot.wind_speed == 8.5
        assert snapshot.pressure == 1013
        assert snapshot.temperature_unit == TemperatureChoices.CELSIUS
        assert snapshot.raw_response == mock_weather_api_response
        assert snapshot.fetched_at is not None

        cache_key = (
            f"{WeatherService.CACHE_KEY_PREFIX}:"
            f"{sample_city.name.lower()}:"
            f"{TemperatureChoices.CELSIUS}"
        )
        cached_id = cache.get(cache_key)
        assert cached_id == snapshot.id


class TestQueryCreation:
    def test_create_query_from_cache(self, sample_city, mock_weather_api_response):
        weather_data = {
            "temperature": 72.5,
            "feels_like": 71.2,
            "weather_description": "clear sky",
            "humidity": 65,
            "wind_speed": 8.5,
            "pressure": 1013,
            "raw_response": mock_weather_api_response,
        }

        snapshot = WeatherService.create_weather_snapshot(
            city=sample_city, weather_data=weather_data, temperature_unit=TemperatureChoices.CELSIUS
        )

        query = WeatherService.create_query(
            snapshot=snapshot, served_from_cache=True, ip_address="192.168.1.1"
        )

        assert query.id is not None
        assert query.weather_snapshot == snapshot
        assert query.served_from_cache is True
        assert query.ip_address == "192.168.1.1"

    def test_create_query_from_api(self, sample_city, mock_weather_api_response):
        weather_data = {
            "temperature": 72.5,
            "feels_like": 71.2,
            "weather_description": "clear sky",
            "humidity": 65,
            "wind_speed": 8.5,
            "pressure": 1013,
            "raw_response": mock_weather_api_response,
        }

        snapshot = WeatherService.create_weather_snapshot(
            city=sample_city, weather_data=weather_data, temperature_unit=TemperatureChoices.CELSIUS
        )

        query = WeatherService.create_query(
            snapshot=snapshot, served_from_cache=False, ip_address="10.0.0.1"
        )

        assert query.served_from_cache is False
        assert query.ip_address == "10.0.0.1"

    def test_create_query_no_ip(self, sample_city, mock_weather_api_response):
        weather_data = {
            "temperature": 72.5,
            "feels_like": 71.2,
            "weather_description": "clear sky",
            "humidity": 65,
            "wind_speed": 8.5,
            "pressure": 1013,
            "raw_response": mock_weather_api_response,
        }

        snapshot = WeatherService.create_weather_snapshot(
            city=sample_city, weather_data=weather_data, temperature_unit=TemperatureChoices.CELSIUS
        )

        query = WeatherService.create_query(
            snapshot=snapshot, served_from_cache=True, ip_address=None
        )

        assert query.ip_address is None


class TestGetWeatherForCity:
    def test_get_weather_city_not_found(self, db):
        cache.clear()

        query, error = WeatherService.get_weather_for_city(
            city_name="Nonexistent City",
            temperature_unit=TemperatureChoices.CELSIUS,
            ip_address="192.168.1.1",
        )

        assert query is None
        assert error == "City 'Nonexistent City' not found in database"

    @patch("weather.services.weather_service.requests.get")
    def test_get_weather_fresh_api_call(self, mock_get, sample_city, mock_weather_api_response):
        cache.clear()
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        query, error = WeatherService.get_weather_for_city(
            city_name="Testopolis",
            temperature_unit=TemperatureChoices.CELSIUS,
            ip_address="192.168.1.1",
        )

        assert query is not None
        assert error is None

        assert query.served_from_cache is False
        assert query.ip_address == "192.168.1.1"

        assert query.weather_snapshot.city_name == "Testopolis"
        assert query.weather_snapshot.temperature == 72.5
        assert query.weather_snapshot.weather_description == "clear sky"

        mock_get.assert_called_once()

    @patch("weather.services.weather_service.requests.get")
    def test_get_weather_from_cache(self, mock_get, sample_city, mock_weather_api_response):
        cache.clear()
        mock_response = Mock()
        mock_response.json.return_value = mock_weather_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        query1, error1 = WeatherService.get_weather_for_city(
            city_name="Testopolis",
            temperature_unit=TemperatureChoices.CELSIUS,
            ip_address="192.168.1.1",
        )

        assert query1 is not None
        assert error1 is None
        assert query1.served_from_cache is False

        mock_get.reset_mock()

        query2, error2 = WeatherService.get_weather_for_city(
            city_name="Testopolis",
            temperature_unit=TemperatureChoices.CELSIUS,
            ip_address="192.168.1.2",
        )

        assert query2 is not None
        assert error2 is None
        assert query2.served_from_cache is True

        mock_get.assert_not_called()
        assert query1.weather_snapshot.id == query2.weather_snapshot.id

    @patch("weather.services.weather_service.requests.get")
    def test_get_weather_api_failure(self, mock_get, sample_city):
        cache.clear()

        mock_get.side_effect = requests.RequestException("API Error")

        query, error = WeatherService.get_weather_for_city(
            city_name="Testopolis",
            temperature_unit=TemperatureChoices.CELSIUS,
            ip_address="192.168.1.1",
        )

        assert query is None
        assert error == "Failed to fetch weather data from API"

    @pytest.mark.parametrize(
        "city_name,search_name",
        [
            ("Testopolis", "Testopolis"),
            ("testopolis", "Testopolis"),
            ("TESTOPOLIS", "Testopolis"),
            ("topo", "Testopolis"),
        ],
    )
    @patch("weather.services.weather_service.requests.get")
    def test_get_weather_case_insensitive_and_search_names(
        self, mock_get, sample_city, mock_weather_api_response, city_name, search_name
    ):
        cache.clear()

        mock_response = Mock()
        mock_response.json.return_value = mock_weather_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        query, error = WeatherService.get_weather_for_city(
            city_name=city_name,
            temperature_unit=TemperatureChoices.CELSIUS,
            ip_address="192.168.1.1",
        )

        assert query is not None
        assert error is None
        assert query.weather_snapshot.city_name == search_name

    @patch("weather.services.weather_service.requests.get")
    def test_get_weather_different_units_different_cache(
        self, mock_get, sample_city, mock_weather_api_response
    ):
        cache.clear()

        mock_response = Mock()
        mock_response.json.return_value = mock_weather_api_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        query1, _ = WeatherService.get_weather_for_city(
            city_name="Testopolis",
            temperature_unit=TemperatureChoices.CELSIUS,
            ip_address="192.168.1.1",
        )

        assert query1.served_from_cache is False

        query2, _ = WeatherService.get_weather_for_city(
            city_name="Testopolis",
            temperature_unit=TemperatureChoices.FAHRENHEIT,
            ip_address="192.168.1.1",
        )

        assert query2.served_from_cache is False
        assert mock_get.call_count == 2

        assert query1.weather_snapshot.id != query2.weather_snapshot.id


class TestEdgeCases:
    def test_build_api_params(self):
        params = WeatherService._build_api_params(lat=37.7749, lon=-122.4194, units="metric")

        assert params["lat"] == 37.7749
        assert params["lon"] == -122.4194
        assert params["units"] == "metric"
        assert "appid" in params

    @patch("weather.services.weather_service.requests.get")
    def test_weather_data_with_missing_optional_fields(self, mock_get, sample_city):
        minimal_response = {
            "main": {"temp": 20.0},
            "weather": [{"description": "cloudy"}],
            "wind": {},
        }

        mock_response = Mock()
        mock_response.json.return_value = minimal_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = WeatherService.fetch_weather_data(
            latitude=37.7749, longitude=-122.4194, temperature_unit=TemperatureChoices.CELSIUS
        )

        assert result is not None
        assert result["temperature"] == 20.0
        assert result["weather_description"] == "cloudy"
        assert result["feels_like"] is None
        assert result["humidity"] is None
        assert result["wind_speed"] is None
        assert result["pressure"] is None

    def test_units_map_coverage(self):
        for choice in TemperatureChoices:
            assert choice in WeatherService.UNITS_MAP
