from django.db.models.query import QuerySet
from django_filters import rest_framework as filters
from rest_framework.filters import BaseFilterBackend
from rest_framework.request import Request
from rest_framework.views import APIView

from weather.models import WeatherQuery


class WeatherQueryFilter(filters.FilterSet):
    
    city = filters.CharFilter(
        field_name='weather_snapshot__city_name',
        lookup_expr='icontains',
        label='City name (case-insensitive)'
    )
    date_from = filters.DateTimeFilter(
        field_name='timestamp',
        lookup_expr='gte',
        label='Date from (inclusive)'
    )
    date_to = filters.DateTimeFilter(
        field_name='timestamp',
        lookup_expr='lte',
        label='Date to (inclusive)'
    )
    
    class Meta:
        model = WeatherQuery
        fields = ['city', 'date_from', 'date_to']
