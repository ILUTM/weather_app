import csv
from typing import Any

from django.db.models import QuerySet
from django.http import HttpResponse

from weather.models import WeatherQuery


class CSVExportService:
    HEADERS = (
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
    )

    @classmethod
    def export_queries_to_csv(cls, queryset: QuerySet[WeatherQuery]) -> HttpResponse:
        """
        Export weather queries to CSV format.

        Args:
            queryset: Filtered QuerySet of WeatherQuery objects

        Returns:
            HttpResponse with CSV file
        """
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="weather_query_history.csv"'
        writer = csv.writer(response)
        writer.writerow(cls.HEADERS)
        for query in queryset.select_related("weather_snapshot"):
            writer.writerow(cls._get_row_data(query))

        return response

    @classmethod
    def _get_row_data(cls, query: WeatherQuery) -> tuple[Any, ...]:
        """
        Extract row data from WeatherQuery object.

        Args:
            query: WeatherQuery instance

        Returns:
            List of values for CSV row
        """
        snapshot = query.weather_snapshot

        return (
            query.id,
            snapshot.city_name,
            snapshot.temperature,
            snapshot.temperature_unit,
            snapshot.feels_like,
            snapshot.weather_description,
            snapshot.humidity,
            snapshot.wind_speed,
            snapshot.pressure,
            "Yes" if query.served_from_cache else "No",
            query.ip_address or "N/A",
            query.timestamp.strftime("%Y-%m-%d %H:%M:%S") if query.timestamp else "N/A",
            snapshot.fetched_at.strftime("%Y-%m-%d %H:%M:%S") if snapshot.fetched_at else "N/A",
        )
