import pytest
from cities_light.models import City, Country, Region


@pytest.fixture
def sample_country(db):
    return Country.objects.create(
        name="United States",
        code2="US",
        code3="USA",
        continent="NA",
        tld="us",
    )


@pytest.fixture
def sample_region(db, sample_country):
    return Region.objects.create(
        name="California",
        name_ascii="California",
        geoname_code="CA",
        country=sample_country,
    )


@pytest.fixture
def sample_city(db, sample_region, sample_country):
    return City.objects.create(
        name="Testopolis",
        name_ascii="testopolis",
        latitude=0,
        longitude=0,
        region=sample_region,
        country=sample_country,
        search_names="testopolis topolis",
    )


@pytest.fixture
def another_city(db, sample_region, sample_country):
    return City.objects.create(
        name="Los Angeles",
        name_ascii="Los Angeles",
        latitude=34.0522,
        longitude=-118.2437,
        region=sample_region,
        country=sample_country,
        search_names="los angeles,la",
    )


@pytest.fixture
def mock_weather_api_response():
    return {
        "coord": {"lon": -122.4194, "lat": 37.7749},
        "weather": [{"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}],
        "base": "stations",
        "main": {
            "temp": 72.5,
            "feels_like": 71.2,
            "temp_min": 68.0,
            "temp_max": 76.0,
            "pressure": 1013,
            "humidity": 65,
        },
        "visibility": 10000,
        "wind": {
            "speed": 8.5,
            "deg": 270,
        },
        "clouds": {"all": 0},
        "dt": 1699200000,
        "sys": {
            "type": 2,
            "id": 2017837,
            "country": "US",
            "sunrise": 1699189200,
            "sunset": 1699227600,
        },
        "timezone": -28800,
        "id": 5391959,
        "name": "San Francisco",
        "cod": 200,
    }


@pytest.fixture
def mock_incomplete_api_response():
    return {
        "coord": {"lon": -122.4194, "lat": 37.7749},
        "cod": 200,
    }
