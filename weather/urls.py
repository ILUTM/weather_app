from django.urls import path

from weather.views import (
    WeatherQueryExportView,
    WeatherQueryHistoryView,
    WeatherView,
)

app_name = "weather"

urlpatterns = [
    path("fetch/", WeatherView.as_view(), name="fetch-weather"),
    path("history/", WeatherQueryHistoryView.as_view(), name="query-history"),
    path("export/", WeatherQueryExportView.as_view(), name="weather-export"),
]
