import csv
from datetime import timedelta
from io import StringIO

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from weather.models import TemperatureChoices, WeatherQuery


@pytest.mark.django_db
class TestWeatherView:

    def test_successful_weather_fetch(self, api_client, sample_city, weather_query, mock_weather_service):
        mock_weather_service.return_value = (weather_query, None)

        url = reverse("weather:fetch-weather")
        data = {"city_name": sample_city.name}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["weather_snapshot"]["city_name"] == sample_city.name
        assert response.data["served_from_cache"] is False

    def test_weather_fetch_with_fahrenheit(self, api_client, sample_city, weather_query, mock_weather_service):
        weather_query.weather_snapshot.temperature = 72.5
        weather_query.weather_snapshot.temperature_unit = TemperatureChoices.FAHRENHEIT
        weather_query.weather_snapshot.save()

        mock_weather_service.return_value = (weather_query, None)

        url = reverse("weather:fetch-weather")
        data = {"city_name": sample_city.name, "temperature_unit": TemperatureChoices.FAHRENHEIT}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["weather_snapshot"]["temperature_unit"] == "F"

    def test_city_not_found(self, api_client, mock_weather_service):
        mock_weather_service.return_value = (None, "City 'NonExistentCity' not found in database")

        url = reverse("weather:fetch-weather")
        data = {"city_name": "NonExistentCity"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "error" in response.data
        assert "not found" in response.data["error"].lower()

    def test_api_error(self, api_client, sample_city, mock_weather_service):
        mock_weather_service.return_value = (None, "Failed to fetch weather data from API")

        url = reverse("weather:fetch-weather")
        data = {"city_name": sample_city.name}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "error" in response.data

    def test_invalid_city_name(self, api_client):
        url = reverse("weather:fetch-weather")
        data = {"city_name": ""}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_city_name(self, api_client):
        url = reverse("weather:fetch-weather")
        data = {}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_temperature_unit(self, api_client, sample_city):
        url = reverse("weather:fetch-weather")
        data = {"city_name": sample_city.name, "temperature_unit": "X"}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cached_weather_data(self, api_client, sample_city, weather_query, mock_weather_service):
        weather_query.served_from_cache = True
        weather_query.save()

        mock_weather_service.return_value = (weather_query, None)

        url = reverse("weather:fetch-weather")
        data = {"city_name": sample_city.name}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["served_from_cache"] is True


@pytest.mark.django_db
class TestWeatherQueryHistoryView:

    def test_get_query_history(self, api_client, weather_query):
        url = reverse("weather:query-history")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert "count" in response.data
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1

    def test_pagination(self, api_client, weather_snapshot, weather_query_factory):
        for i in range(15):
            weather_query_factory(
                snapshot=weather_snapshot,
                served_from_cache=False,
                ip_address=f"192.168.1.{i}",
            )

        url = reverse("weather:query-history")
        response = api_client.get(url, {"page_size": 5})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 15
        assert len(response.data["results"]) == 5
        assert response.data["next"] is not None

    def test_filter_by_city(self, api_client, sample_city, another_city, weather_snapshot_factory, weather_query_factory):
        snapshot1 = weather_snapshot_factory(city=sample_city)
        snapshot2 = weather_snapshot_factory(city=another_city, temperature=25.0, weather_description="sunny")

        weather_query_factory(snapshot=snapshot1, ip_address="192.168.1.1")
        weather_query_factory(snapshot=snapshot2, ip_address="192.168.1.2")

        url = reverse("weather:query-history")
        response = api_client.get(url, {"city": sample_city.name})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["city_name"] == sample_city.name

    def test_filter_by_city_case_insensitive(self, api_client, sample_city, weather_snapshot_factory, weather_query_factory):
        snapshot = weather_snapshot_factory(city=sample_city)
        weather_query_factory(snapshot=snapshot, ip_address="192.168.1.1")

        url = reverse("weather:query-history")
        response = api_client.get(url, {"city": sample_city.name.upper()})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_filter_by_date_range(self, api_client, weather_snapshot, weather_query_factory):
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        two_days_ago = now - timedelta(days=2)

        weather_query_factory(snapshot=weather_snapshot, ip_address="192.168.1.1", timestamp=two_days_ago)
        weather_query_factory(snapshot=weather_snapshot, ip_address="192.168.1.2", timestamp=yesterday)
        weather_query_factory(snapshot=weather_snapshot, ip_address="192.168.1.3", timestamp=now)

        url = reverse("weather:query-history")
        response = api_client.get(
            url,
            {
                "date_from": yesterday.isoformat(),
                "date_to": now.isoformat(),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 2

    def test_combined_filters(self, api_client, sample_city, another_city, weather_snapshot_factory, weather_query_factory):
        now = timezone.now()
        yesterday = now - timedelta(days=1)

        snapshot1 = weather_snapshot_factory(city=sample_city)
        snapshot2 = weather_snapshot_factory(city=another_city, temperature=25.0, weather_description="sunny")

        weather_query_factory(snapshot=snapshot1, ip_address="192.168.1.1", timestamp=yesterday)
        weather_query_factory(snapshot=snapshot1, ip_address="192.168.1.2", timestamp=now)
        weather_query_factory(snapshot=snapshot2, ip_address="192.168.1.3", timestamp=now)

        url = reverse("weather:query-history")
        response = api_client.get(
            url,
            {
                "city": sample_city.name,
                "date_from": now.isoformat(),
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["city_name"] == sample_city.name

    def test_empty_results(self, api_client):
        url = reverse("weather:query-history")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 0
        assert len(response.data["results"]) == 0

    def test_custom_page_size(self, api_client, weather_snapshot, weather_query_factory):
        for i in range(25):
            weather_query_factory(snapshot=weather_snapshot, ip_address=f"192.168.1.{i}")

        url = reverse("weather:query-history")
        response = api_client.get(url, {"page_size": 20})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 20

    def test_max_page_size_limit(self, api_client, weather_snapshot, weather_query_factory):
        for i in range(150):
            weather_query_factory(snapshot=weather_snapshot, ip_address=f"192.168.1.{i % 255}")

        url = reverse("weather:query-history")
        response = api_client.get(url, {"page_size": 150})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 100


@pytest.mark.django_db
class TestWeatherQueryExportView:
    def test_export_csv(self, api_client, weather_query):
        url = reverse("weather:weather-export")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "text/csv"
        assert "attachment" in response["Content-Disposition"]
        assert "weather_query_history.csv" in response["Content-Disposition"]

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        assert len(rows) == 2
        assert rows[0][0] == "Query ID"
        assert rows[0][1] == "City Name"

    def test_export_csv_with_multiple_queries(self, api_client, weather_snapshot, weather_query_factory):
        for i in range(5):
            weather_query_factory(
                snapshot=weather_snapshot,
                served_from_cache=bool(i % 2),
                ip_address=f"192.168.1.{i}",
            )

        url = reverse("weather:weather-export")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        assert len(rows) == 6

    def test_export_csv_data_format(self, api_client, weather_snapshot, weather_query_factory):
        query = weather_query_factory(
            snapshot=weather_snapshot,
            served_from_cache=True,
            ip_address="192.168.1.100",
        )

        url = reverse("weather:weather-export")
        response = api_client.get(url)

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        next(csv_reader)
        data_row = next(csv_reader)

        assert data_row[0] == str(query.id)
        assert data_row[1] == weather_snapshot.city_name
        assert data_row[2] == str(weather_snapshot.temperature)
        assert data_row[3] == weather_snapshot.temperature_unit
        assert data_row[9] == "Yes"

    def test_export_csv_filter_by_city(self, api_client, sample_city, another_city, weather_snapshot_factory, weather_query_factory):
        snapshot1 = weather_snapshot_factory(city=sample_city)
        snapshot2 = weather_snapshot_factory(city=another_city, temperature=25.0, weather_description="sunny")

        weather_query_factory(snapshot=snapshot1, ip_address="192.168.1.1")
        weather_query_factory(snapshot=snapshot2, ip_address="192.168.1.2")

        url = reverse("weather:weather-export")
        response = api_client.get(url, {"city": sample_city.name})

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        assert len(rows) == 2
        assert sample_city.name in rows[1][1]

    def test_export_csv_no_pagination(self, api_client, weather_snapshot, weather_query_factory):
        for i in range(150):
            weather_query_factory(snapshot=weather_snapshot, ip_address=f"192.168.1.{i % 255}")

        url = reverse("weather:weather-export")
        response = api_client.get(url)

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        assert len(rows) == 151

    def test_export_csv_cache_indicator(self, api_client, weather_snapshot, weather_query_factory):
        weather_query_factory(snapshot=weather_snapshot, served_from_cache=True, ip_address="192.168.1.1")
        weather_query_factory(snapshot=weather_snapshot, served_from_cache=False, ip_address="192.168.1.2")

        url = reverse("weather:weather-export")
        response = api_client.get(url)

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        next(csv_reader)
        row1 = next(csv_reader)
        row2 = next(csv_reader)
        assert "Yes" in [row1[9], row2[9]]
        assert "No" in [row1[9], row2[9]]
