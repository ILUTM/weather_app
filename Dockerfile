FROM python:3.11.2-slim

RUN mkdir /app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y netcat && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.8.0 \
    && poetry config virtualenvs.create false

COPY pyproject.toml /app

RUN poetry install --no-root

COPY . .

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]