from django.apps import AppConfig


class WeatherConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "weather"

    def ready(self) -> None:
        from health_check.plugins import plugin_dir

        from weather.health_check import WeatherAPIHealthCheck

        plugin_dir.register(WeatherAPIHealthCheck)
