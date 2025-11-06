from django.urls import path

from weather.views import WeatherQueryHistoryView, WeatherView

app_name = "weather"

urlpatterns = [
    path("fetch/", WeatherView.as_view(), name="fetch-weather"),
    path("history/", WeatherQueryHistoryView.as_view(), name="query-history"),
]
