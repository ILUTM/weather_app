import csv
from datetime import timedelta
from io import StringIO

import pytest
from django.http import HttpResponse
from django.utils import timezone

from weather.models import TemperatureChoices, WeatherQuery
from weather.services.csv_export_service import CSVExportService


@pytest.mark.django_db
class TestCSVExportService:
    def test_export_single_query(self, weather_query):
        queryset = WeatherQuery.objects.filter(id=weather_query.id)
        response = CSVExportService.export_queries_to_csv(queryset)

        assert isinstance(response, HttpResponse)
        assert response["Content-Type"] == "text/csv"
        assert 'attachment; filename="weather_query_history.csv"' in response["Content-Disposition"]

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        assert len(rows) == 2
        assert rows[0] == list(CSVExportService.HEADERS)

    def test_export_multiple_queries(self, weather_snapshot, weather_query_factory):
        queries = [
            weather_query_factory(snapshot=weather_snapshot, ip_address=f"192.168.1.{i}")
            for i in range(5)
        ]

        queryset = WeatherQuery.objects.filter(id__in=[q.id for q in queries])
        response = CSVExportService.export_queries_to_csv(queryset)

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        assert len(rows) == 6

    def test_export_empty_queryset(self):
        queryset = WeatherQuery.objects.none()
        response = CSVExportService.export_queries_to_csv(queryset)

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        assert len(rows) == 1
        assert rows[0] == list(CSVExportService.HEADERS)

    def test_csv_headers_correct(self, weather_query):
        queryset = WeatherQuery.objects.filter(id=weather_query.id)
        response = CSVExportService.export_queries_to_csv(queryset)

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        headers = next(csv_reader)

        expected_headers = [
            "Query ID",
            "City Name",
            "Temperature",
            "Temperature Unit",
            "Feels Like",
            "Weather Description",
            "Humidity (%)",
            "Wind Speed",
            "Pressure (hPa)",
            "Served From Cache",
            "IP Address",
            "Query Time",
            "Data Fetched At",
        ]

        assert headers == expected_headers

    def test_row_data_format(self, weather_snapshot, weather_query_factory):
        query = weather_query_factory(
            snapshot=weather_snapshot,
            served_from_cache=True,
            ip_address="192.168.1.100",
        )

        queryset = WeatherQuery.objects.filter(id=query.id)
        response = CSVExportService.export_queries_to_csv(queryset)

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        next(csv_reader)
        data_row = next(csv_reader)

        assert data_row[0] == str(query.id)
        assert data_row[1] == weather_snapshot.city_name
        assert data_row[2] == str(weather_snapshot.temperature)
        assert data_row[3] == weather_snapshot.temperature_unit
        assert data_row[4] == str(weather_snapshot.feels_like)
        assert data_row[5] == weather_snapshot.weather_description
        assert data_row[6] == str(weather_snapshot.humidity)
        assert data_row[7] == str(weather_snapshot.wind_speed)
        assert data_row[8] == str(weather_snapshot.pressure)
        assert data_row[9] == "Yes"
        assert data_row[10] == "192.168.1.100"
        assert data_row[11] == query.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        assert data_row[12] == weather_snapshot.fetched_at.strftime("%Y-%m-%d %H:%M:%S")

    def test_cache_indicator_yes(self, weather_snapshot, weather_query_factory):
        query = weather_query_factory(snapshot=weather_snapshot, served_from_cache=True)
        row_data = CSVExportService._get_row_data(query)
        assert row_data[9] == "Yes"

    def test_cache_indicator_no(self, weather_snapshot, weather_query_factory):
        query = weather_query_factory(snapshot=weather_snapshot, served_from_cache=False)
        row_data = CSVExportService._get_row_data(query)
        assert row_data[9] == "No"

    def test_null_ip_address(self, weather_snapshot, weather_query_factory):
        query = weather_query_factory(snapshot=weather_snapshot, ip_address=None)

        row_data = CSVExportService._get_row_data(query)

        assert row_data[10] == "N/A"

    def test_temperature_units(self, sample_city, weather_snapshot_factory, weather_query_factory):
        snapshot_celsius = weather_snapshot_factory(
            city=sample_city,
            temperature=20.0,
            temperature_unit=TemperatureChoices.CELSIUS,
        )
        snapshot_fahrenheit = weather_snapshot_factory(
            city=sample_city,
            temperature=68.0,
            temperature_unit=TemperatureChoices.FAHRENHEIT,
        )

        query_celsius = weather_query_factory(snapshot=snapshot_celsius)
        query_fahrenheit = weather_query_factory(snapshot=snapshot_fahrenheit)

        row_celsius = CSVExportService._get_row_data(query_celsius)
        row_fahrenheit = CSVExportService._get_row_data(query_fahrenheit)

        assert row_celsius[3] == TemperatureChoices.CELSIUS
        assert row_fahrenheit[3] == TemperatureChoices.FAHRENHEIT

    def test_datetime_formatting(self, weather_snapshot, weather_query_factory):
        specific_time = timezone.now().replace(
            year=2024, month=3, day=15, hour=14, minute=30, second=45, microsecond=0
        )
        query = weather_query_factory(snapshot=weather_snapshot, timestamp=specific_time)

        row_data = CSVExportService._get_row_data(query)

        assert row_data[11] == "2024-03-15 14:30:45"

    def test_special_characters_in_city_name(
        self, sample_region, sample_country, weather_snapshot_factory, weather_query_factory
    ):
        from cities_light.models import City

        city_with_special_chars = City.objects.create(
            name="São Paulo",
            name_ascii="Sao Paulo",
            latitude=-23.5505,
            longitude=-46.6333,
            region=sample_region,
            country=sample_country,
            search_names="sao paulo",
        )

        snapshot = weather_snapshot_factory(city=city_with_special_chars)
        query = weather_query_factory(snapshot=snapshot)

        row_data = CSVExportService._get_row_data(query)

        assert row_data[1] == "São Paulo"

    def test_special_characters_in_description(
        self, sample_city, weather_snapshot_factory, weather_query_factory
    ):
        snapshot = weather_snapshot_factory(
            city=sample_city, weather_description="Heavy rain & wind, 50°C"
        )
        query = weather_query_factory(snapshot=snapshot)
        row_data = CSVExportService._get_row_data(query)
        assert row_data[5] == "Heavy rain & wind, 50°C"

    def test_large_dataset_export(self, weather_snapshot, weather_query_factory):
        queries = [
            weather_query_factory(snapshot=weather_snapshot, ip_address=f"192.168.1.{i % 255}")
            for i in range(1000)
        ]

        queryset = WeatherQuery.objects.filter(id__in=[q.id for q in queries])
        response = CSVExportService.export_queries_to_csv(queryset)

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        rows = list(csv_reader)

        assert len(rows) == 1001

    def test_queryset_ordering_preserved(self, weather_snapshot, weather_query_factory):
        now = timezone.now()
        queries = [
            weather_query_factory(
                snapshot=weather_snapshot,
                timestamp=now - timedelta(days=i),
                ip_address=f"192.168.1.{i}",
            )
            for i in range(5)
        ]

        queryset = WeatherQuery.objects.filter(id__in=[q.id for q in queries]).order_by(
            "-timestamp"
        )

        response = CSVExportService.export_queries_to_csv(queryset)

        content = response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(content))
        next(csv_reader)
        rows = list(csv_reader)

        ip_addresses = [row[10] for row in rows]
        assert ip_addresses == [
            "192.168.1.0",
            "192.168.1.1",
            "192.168.1.2",
            "192.168.1.3",
            "192.168.1.4",
        ]

    def test_select_related_optimization(
        self, weather_snapshot, weather_query_factory, django_assert_num_queries
    ):
        for i in range(10):
            weather_query_factory(snapshot=weather_snapshot, ip_address=f"192.168.1.{i}")

        queryset = WeatherQuery.objects.all()

        with django_assert_num_queries(1):
            response = CSVExportService.export_queries_to_csv(queryset)
            _ = response.content

    def test_get_row_data_all_fields(self, weather_query):
        row_data = CSVExportService._get_row_data(weather_query)

        assert len(row_data) == len(CSVExportService.HEADERS)
        assert all(field is not None for field in row_data)

    def test_decimal_precision(self, sample_city, weather_snapshot_factory, weather_query_factory):
        snapshot = weather_snapshot_factory(
            city=sample_city,
            temperature=20.567,
            feels_like=19.432,
            wind_speed=5.789,
        )
        query = weather_query_factory(snapshot=snapshot)

        row_data = CSVExportService._get_row_data(query)

        assert row_data[2] == 20.567
        assert row_data[4] == 19.432
        assert row_data[7] == 5.789

    def test_content_type_header(self, weather_query):
        queryset = WeatherQuery.objects.filter(id=weather_query.id)
        response = CSVExportService.export_queries_to_csv(queryset)

        assert response["Content-Type"] == "text/csv"

    def test_content_disposition_header(self, weather_query):
        queryset = WeatherQuery.objects.filter(id=weather_query.id)
        response = CSVExportService.export_queries_to_csv(queryset)

        assert "attachment" in response["Content-Disposition"]
        assert "weather_query_history.csv" in response["Content-Disposition"]
