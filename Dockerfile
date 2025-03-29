FROM python:3.12-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV POETRY_CACHE_DIR=/app/.cache

RUN pip install --upgrade pip \
    && pip install poetry


WORKDIR /app

COPY pyproject.toml poetry.lock* /app/

RUN poetry install --no-interaction --no-ansi --no-root

COPY . /app

USER 1000

CMD ["poetry", "run", "python", "src/discord_radio_bot/main.py"]