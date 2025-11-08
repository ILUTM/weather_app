from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.get_client_ip import get_client_ip
from common.pagination import WeatherQueryPagination
from weather.filters import WeatherQueryFilter
from weather.models import TemperatureChoices, WeatherQuery
from weather.serializers import (
    WeatherQueryHistorySerializer,
    WeatherQuerySerializer,
    WeatherRequestSerializer,
)
from weather.services.csv_export_service import CSVExportService
from weather.services.weather_service import WeatherService


class WeatherView(APIView):
    @extend_schema(
        request=WeatherRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=WeatherQuerySerializer,
                description="Weather data successfully retrieved",
                examples=[
                    OpenApiExample(
                        "Success Response",
                        value={
                            "id": 1,
                            "weather_snapshot": {
                                "id": 1,
                                "city_name": "Minsk",
                                "temperature": 15.5,
                                "feels_like": 14.2,
                                "weather_description": "clear sky",
                                "humidity": 65,
                                "wind_speed": 3.5,
                                "pressure": 1013,
                                "temperature_unit": "C",
                                "fetched_at": "2025-11-05T12:00:00Z",
                            },
                            "timestamp": "2025-11-05T12:00:00Z",
                            "served_from_cache": False,
                        },
                    )
                ],
            ),
            400: OpenApiResponse(description="Invalid city name"),
            404: OpenApiResponse(description="City not found"),
            500: OpenApiResponse(description="Weather API error"),
        },
        summary="Get weather for a city",
        description="Fetch current weather data for a specified city."
        "The data is cached for 5 minutes.",
    )
    def post(self, request: Request) -> Response:
        serializer = WeatherRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        city_name = serializer.validated_data["city_name"]
        temperature_unit = serializer.validated_data.get(
            "temperature_unit", TemperatureChoices.CELSIUS
        )
        ip_address = get_client_ip(request)
        query, error = WeatherService.get_weather_for_city(city_name, temperature_unit, ip_address)

        if error:
            status_code = (
                status.HTTP_404_NOT_FOUND
                if "not found" in error.lower()
                else status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response({"error": error}, status=status_code)

        serializer = WeatherQuerySerializer(query)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WeatherQueryHistoryView(generics.ListAPIView):
    queryset = WeatherQuery.objects.select_related("weather_snapshot").all()
    serializer_class = WeatherQueryHistorySerializer
    filterset_class = WeatherQueryFilter
    filter_backends = (DjangoFilterBackend,)
    pagination_class = WeatherQueryPagination

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="page",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Page number",
                default=1,
            ),
            OpenApiParameter(
                name="page_size",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Number of results per page (max 100)",
                default=10,
            ),
            OpenApiParameter(
                name="city",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by city name (case-insensitive substring match)",
                required=False,
            ),
            OpenApiParameter(
                name="date_from",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter queries from this date/time (ISO 8601 format)",
                required=False,
                examples=[OpenApiExample("Date from example", value="2025-11-01T00:00:00Z")],
            ),
            OpenApiParameter(
                name="date_to",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter queries up to this date/time (ISO 8601 format)",
                required=False,
                examples=[OpenApiExample("Date to example", value="2025-11-30T23:59:59Z")],
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=WeatherQueryHistorySerializer(many=True),
                description="Paginated list of weather queries",
                examples=[
                    OpenApiExample(
                        "Query History Response",
                        value={
                            "count": 25,
                            "next": "http://api.example.com/weather/history/?page=2",
                            "previous": None,
                            "results": [
                                {
                                    "id": 1,
                                    "city_name": "Horad Zhodzina",
                                    "temperature": 15.5,
                                    "weather_description": "clear sky",
                                    "temperature_unit": "C",
                                    "timestamp": "2025-11-05T12:00:00Z",
                                    "served_from_cache": False,
                                },
                                {
                                    "id": 2,
                                    "city_name": "Minsk",
                                    "temperature": 14.0,
                                    "weather_description": "cloudy",
                                    "temperature_unit": "C",
                                    "timestamp": "2025-11-05T11:30:00Z",
                                    "served_from_cache": True,
                                },
                            ],
                        },
                    )
                ],
            )
        },
        summary="Get query history",
        description=(
            "Retrieve a paginated list of weather queries with optional filtering.\n\n"
            "**Filters:**\n"
            "- `city`: Case-insensitive substring match on city name\n"
            "- `date_from`: Show queries from this date/time onwards\n"
            "- `date_to`: Show queries up to this date/time\n\n"
            "**Examples:**\n"
            "- `/weather/history/?city=minsk` - All queries for cities containing 'minsk'\n"
            "- `/weather/history/?date_from=2025-11-01T00:00:00Z&"
            "date_to=2025-11-30T23:59:59Z` - Queries in November 2025\n"
            "- `/weather/history/?city=minsk&page=2&page_size=20`"
            "- Second page with 20 results per page"
        ),
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)


class WeatherQueryExportView(generics.ListAPIView):
    queryset = WeatherQuery.objects.select_related("weather_snapshot").all()
    serializer_class = WeatherQueryHistorySerializer
    filterset_class = WeatherQueryFilter
    filter_backends = (DjangoFilterBackend,)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="city",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by city name (case-insensitive substring match)",
                required=False,
            ),
            OpenApiParameter(
                name="date_from",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter queries from this date/time (ISO 8601 format)",
                required=False,
                examples=[OpenApiExample("Date from example", value="2025-11-01T00:00:00Z")],
            ),
            OpenApiParameter(
                name="date_to",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter queries up to this date/time (ISO 8601 format)",
                required=False,
                examples=[OpenApiExample("Date to example", value="2025-11-30T23:59:59Z")],
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="CSV file with weather query history",
                examples=[
                    OpenApiExample(
                        "CSV Export",
                        value=(
                            "Query ID,City Name,Temperature,Temperature Unit,..."
                            "\n1,Minsk,15.5,C,..."
                        ),
                    )
                ],
            )
        },
        summary="Export query history to CSV",
        description=(
            "Export weather queries to CSV file with optional filtering.\n\n"
            "**Filters:** (same as history endpoint)\n"
            "- `city`: Case-insensitive substring match on city name\n"
            "- `date_from`: Show queries from this date/time onwards\n"
            "- `date_to`: Show queries up to this date/time\n\n"
            "**Examples:**\n"
            "- `/weather/export/?city=minsk` - Export all Minsk queries\n"
            "- `/weather/export/?date_from=2025-11-01T00:00:00Z` - Export November onwards\n\n"
            "**Note:** Export includes ALL matching records (no pagination)"
        ),
    )
    def get(self, request: Request, *args, **kwargs) -> HttpResponse:
        queryset = self.filter_queryset(self.get_queryset())
        return CSVExportService.export_queries_to_csv(queryset)
