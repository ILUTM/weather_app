from rest_framework import serializers

from weather.models import TemperatureChoices, WeatherQuery, WeatherSnapshot


class WeatherRequestSerializer(serializers.Serializer):
    city_name = serializers.CharField(
        max_length=255,
        help_text="Name of the city to fetch weather for",
        required=True,
    )
    temperature_unit = serializers.ChoiceField(
        choices=TemperatureChoices.choices,
        default=TemperatureChoices.CELSIUS,
        help_text="Temperature unit (C for Celsius, F for Fahrenheit, K for Kelvin)",
        required=False,
    )


class WeatherSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherSnapshot
        fields = [
            "id",
            "city_name",
            "temperature",
            "feels_like",
            "weather_description",
            "humidity",
            "wind_speed",
            "pressure",
            "temperature_unit",
            "fetched_at",
        ]


class WeatherQuerySerializer(serializers.ModelSerializer):
    weather_snapshot = WeatherSnapshotSerializer(read_only=True)

    class Meta:
        model = WeatherQuery
        fields = [
            "id",
            "weather_snapshot",
            "timestamp",
            "served_from_cache",
        ]


class WeatherQueryHistorySerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="weather_snapshot.city_name")
    temperature = serializers.FloatField(source="weather_snapshot.temperature")
    weather_description = serializers.CharField(source="weather_snapshot.weather_description")
    temperature_unit = serializers.CharField(source="weather_snapshot.temperature_unit")

    class Meta:
        model = WeatherQuery
        fields = [
            "id",
            "city_name",
            "temperature",
            "weather_description",
            "temperature_unit",
            "timestamp",
            "served_from_cache",
        ]
