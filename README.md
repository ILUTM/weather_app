# ☁️ Weather App: Real-Time & Historical Data API

This **Django/DRF** application provides real-time and historical weather data. It serves as an API gateway, fetching data from the **OpenWeatherMap API**, storing query history in a **PostgreSQL** database, and providing a web interface. Key features include **API rate-limiting**, **health checks**, and comprehensive documentation via **Swagger UI**.

## 💻 Technology Stack

* **Backend:** Python 3.11+, Django 5.2, Django REST Framework (DRF)
* **Database:** PostgreSQL 15
* **Package Management:** Poetry
* **Development Tools:** Docker, Docker Compose
* **Linting/Typing:** Ruff, Mypy, `django-stubs`
* **Testing:** Pytest, pytest-django, pytest-cov

## Getting Started

Follow these steps to successfully set up and run the project using `docker-compose`.

### Install Docker and Docker Compose

Before you begin, make sure you have Docker and Docker Compose installed on your system.

### Environment Setup

Create a `.env` file in the project root with the following variables:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DB_NAME=weather_db
DB_USER=postgres
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# OpenWeatherMap API
WEATHER_API_KEY=your-openweathermap-api-key
WEATHER_API_BASE_URL=https://api.openweathermap.org/data/2.5/weather
WEATHER_CACHE_TTL=300

# Rate Limiting
RATE_LIMIT_REQUESTS=30
RATE_PERIOD=60
```

**Note:** Get your OpenWeatherMap API key at [openweathermap.org/api](https://openweathermap.org/api)

### Supported Countries Configuration

The application uses `django-cities-light` to provide city data. **By default, only US and BY (Belarus) cities are included.**

To add support for weather queries in additional countries:

1. **Update the `.env` file:**
```env
   CITIES_LIGHT_COUNTRIES=US,BY,GB,FR,DE  
```
   
   Use [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) country codes (e.g., `GB` for United Kingdom, `FR` for France, `DE` for Germany).

2. **Reload city data:**
```bash
   docker exec -it weather-app poetry run python manage.py cities_light --force-all
```

3. **Restart the application:**
```bash
   docker compose -f docker-compose.yml restart
```

**Note:** Adding many countries will increase the database size and initial load time. The city database contains only cities with population data (types: PPL, PPLA, PPLA2, PPLA3, PPLA4, PPLC).


### Running the Services

1.  Clone the repository:
    ```bash
    git clone https://github.com/ILUTM/weather_app.git
    cd weather_app
    ```

2.  Start the services (application and database):
    ```bash
    docker compose -f docker-compose.yml up
    ```
    
    Or run in detached mode:
    ```bash
    docker compose -f docker-compose.yml up -d
    ```

**Note:** Migrations and city data loading happen automatically via `entrypoint.sh` on container startup.

### Stopping the Services

```bash
docker compose -f docker-compose.yml down
```

To remove volumes as well:
```bash
docker compose -f docker-compose.yml down -v
```
   
### Commands

All commands which we want to use in our project we should use inside container.

Examples:
```bash
# Run tests
docker exec -it weather-app pytest -v -s

# Django management commands
docker exec -it weather-app poetry run python manage.py shell
docker exec -it weather-app poetry run python manage.py makemigrations

# Run linting
docker exec -it weather-app poetry run ruff check .
docker exec -it weather-app poetry run mypy .
```

## Usage

### API Documentation (Swagger UI)
You can access endpoints and try them with Swagger UI. See the link below:
    
```
http://localhost:8000/api/docs
```

### Web Interface
Access the web interface for weather queries:
```
http://localhost:8000/
```

### Health Check
Check application health status:
```
http://localhost:8000/health/
```

### Key API Endpoints

- `GET /api/weather/current/` - Get current weather for a city
- `GET /api/weather/history/` - View weather query history
- `GET /api/weather/export/` - Export history as CSV
- `GET /api/cities/` - Search cities

## Test

To run tests for the service use command for the running container:

```bash
docker exec -it weather-app pytest -vvv
```

Run tests with coverage:
```bash
docker exec -it weather-app pytest --cov=. --cov-report=html
```

Run specific test file:
```bash
docker exec -it weather-app pytest tests/weather/test_views.py -v
```

## Contributing

Before starting work on a new task, pull the recent changes to your local dev branch with git:

```bash
git switch dev
git pull
```

Then create a new branch starting with word **feature**, **refactor**, **fix**, etc, depending on your task. Provide number of the task and its short name. For example:

```bash
git checkout -b feature/3/name-of-task
```

To push your changes to the GitLab use command git push. For instance:

```bash
git push origin feature/3/name-of-task
```

After that you can create merge request to the dev branch using GitLab.

Before creating merge request it's better to ensure your code satisfies configuration of ruff linter and mypy analyzer. To use them locally run the commands:

```bash
poetry run ruff check .
poetry run mypy .
```

Fix auto-fixable linting issues:
```bash
poetry run ruff check --fix .
```

Also make sure all the tests are passed:
```bash
poetry run pytest tests/
```

### Commit Message Convention

Follow conventional commits format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

Example: `feat: add weather alerts functionality`

## Troubleshooting

### Database Connection Issues
```bash
docker ps | grep weather_app_db

docker logs weather_app_db

docker compose -f docker-compose.yml restart db
```

### Application Not Starting
```bash
docker logs weather-app

docker compose -f docker-compose.yml restart
```

### Port Already in Use

If port 8000 or 5432 is already in use, update the ports in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000" 
```