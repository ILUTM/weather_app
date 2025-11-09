from django.urls import path

from weather.views import HistoryPageView, WeatherPageView

app_name = "weather_web"

urlpatterns = [
    path("", WeatherPageView.as_view(), name="fetch-weather-page"),
    path("history/", HistoryPageView.as_view(), name="history-page"),
]
