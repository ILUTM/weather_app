# ☁️ Weather App: Real-Time & Historical Data API

This **Django/DRF** application provides real-time and historical weather data. It serves as an API gateway, fetching data from the **OpenWeatherMap API**, storing query history in a **PostgreSQL** database, and providing a web interface. Key features include **API rate-limiting** and comprehensive documentation via **Swagger UI**.

## 💻 Technology Stack

* **Backend:** Python, Django, Django REST Framework (DRF)
* **Database:** PostgreSQL
* **Package Management:** Poetry
* **Development Tools:** Docker, Docker Compose
* **Linting/Typing:** Ruff, Mypy, `django-stubs`


## Getting Started

Follow these steps to successfully set up and run the project using `docker-compose`.

### Install Docker and Docker Compose

Before you begin, make sure you have Docker and Docker Compose installed on your system.

### Running the Services

1.  Clone the repository:
    ```bash
    git clone https://github.com/ILUTM/weather_app.git
    cd weather_app
    ```
2.  Start the services (application and database):
    ```bash
    docker compose up -d 
    ```
    Or

    ```bash
    docker compose -f docker-compose.yml up
    ```
   
### Commands
All commands which we want to use in our project we should use inside container, see makefile

Example:
   ```bash
   docker exec -it weather-app pytest -v -s
   ```

## Usage

You can access endpoints and try them with Swagger UI. See the link below:
    
    http://localhost:8000/api/docs


### Test

To run tests for the service use command for the running container:

```bash
docker exec -it weather-app pytest -vvv
```

## Contributing

Before starting work on a new task, pull the recent changes to your local dev branch with git:

```bash
git switch dev
git pull
```

Then create a new branch starting with word **feature**, **refactor**, **fix**, etc, depending on your task. Provide number of the task and it's short name. For example:

```bash
git checkout -b feature/3/name-of-task
```

To push your changes to the GitLab use command git push. For instance:

```bash
git push origin feature/3/name-of-task
```

After that you can create merge request to the dev branch using GitLab.
Before creating merge request it's better to ensure your code satisfies configuration of flake8 linter and mypy analyzer. To use them locally run the commands:

```bash
poetry run ruff check .
poetry run mypy .
```
Also make sure all the tests are passed.
```bash
poetry run pytest tests.
```
