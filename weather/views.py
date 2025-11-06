from typing import cast

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from weather.models import TemperatureChoices, WeatherQuery
from weather.serializers import (
    WeatherQueryHistorySerializer,
    WeatherQuerySerializer,
    WeatherRequestSerializer,
)
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
        ip_address = self._get_client_ip(request)
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

    def _get_client_ip(self, request: Request) -> str | None:
        """Extract client IP address from request."""
        x_forwarded_for = cast(str | None, request.META.get("HTTP_X_FORWARDED_FOR"))
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return cast(str | None, request.META.get("REMOTE_ADDR"))


class WeatherQueryHistoryView(APIView):
    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=WeatherQueryHistorySerializer(many=True),
                description="List of weather queries",
                examples=[
                    OpenApiExample(
                        "Query History Response",
                        value=[
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
                    )
                ],
            )
        },
        summary="Get query history",
        description="Retrieve a list of all weather queries with their associated weather data.",
    )
    def get(self, request: Request) -> Response:
        """Get all weather queries."""
        queries = WeatherQuery.objects.select_related("weather_snapshot").all()
        serializer = WeatherQueryHistorySerializer(queries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
