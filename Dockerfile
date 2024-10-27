FROM python:3.12.2-slim-bookworm

ENV PROJECT_ROOT /app
WORKDIR $PROJECT_ROOT/appsec-discovery

RUN apt update && apt install -y git gcc g++
RUN pip install poetry

COPY appsec-discovery/pyproject.toml $PROJECT_ROOT/appsec-discovery
COPY appsec-discovery/*.lock $PROJECT_ROOT/appsec-discovery

RUN poetry config virtualenvs.create false
RUN poetry update && poetry install --no-root

WORKDIR $PROJECT_ROOT

COPY . $PROJECT_ROOT

RUN PATH="$PROJECT_ROOT/bin:$PATH"
RUN PYTHONPATH="$PROJECT_ROOT/appsec-discovery:$PYTHONPATH"