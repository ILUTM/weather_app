from cities_light.models import City
from django.db import models
from django.utils import timezone


class TemperatureChoices(models.TextChoices):
    CELSIUS = "C", "Celsius"
    FAHRENHEIT = "F", "Fahrenheit"
    KELVIN = "K", "Kelvin"


class WeatherSnapshot(models.Model):
    city_name = models.CharField(max_length=255, db_index=True)
    city = models.ForeignKey(
        City, on_delete=models.SET_NULL, null=True, blank=True, related_name="weather_snapshots"
    )

    temperature = models.FloatField()
    feels_like = models.FloatField(null=True, blank=True)
    weather_description = models.CharField(max_length=255)
    humidity = models.IntegerField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    pressure = models.IntegerField(null=True, blank=True)

    temperature_unit = models.CharField(
        max_length=1,
        choices=TemperatureChoices.choices,
        default=TemperatureChoices.CELSIUS,
        db_index=True,
    )

    raw_response = models.JSONField(null=True, blank=True)
    fetched_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-fetched_at"]
        indexes = [
            models.Index(fields=["city_name", "temperature_unit", "-fetched_at"]),
            models.Index(fields=["-fetched_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.city_name} - {self.temperature}°{self.temperature_unit}"


class WeatherQuery(models.Model):
    weather_snapshot = models.ForeignKey(
        WeatherSnapshot, on_delete=models.CASCADE, related_name="queries"
    )

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    served_from_cache = models.BooleanField(default=False, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["ip_address", "-timestamp"]),
            models.Index(fields=["served_from_cache"]),
        ]

    def __str__(self) -> str:
        cache_indicator = " (cached)" if self.served_from_cache else ""
        return f"Query for {self.weather_snapshot.city_name} at {self.timestamp}{cache_indicator}"
