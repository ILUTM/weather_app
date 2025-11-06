from typing import TypedDict


class WeatherData(TypedDict):
    temperature: float
    feels_like: float | None
    weather_description: str
    humidity: int | None
    wind_speed: float | None
    pressure: int | None
    raw_response: dict
