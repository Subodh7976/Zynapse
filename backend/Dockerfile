FROM python:3.12-slim AS builder

RUN pip install --upgrade pip && pip install poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry lock
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --verbose
RUN poetry run pip install uv

FROM python:3.12-slim AS runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY ./app .

RUN uvx --version

EXPOSE 8000