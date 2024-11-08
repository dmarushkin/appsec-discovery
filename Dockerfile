FROM python:3.12.2-slim-bookworm

ENV PROJECT_ROOT /app
WORKDIR $PROJECT_ROOT

RUN apt update && apt install -y git gcc g++ curl apt-transport-https ca-certificates gnupg-agent software-properties-common curl

# install docker in docker
RUN curl -fsSL https://get.docker.com | sh

# install poetry and appsec discovery cli deps
RUN pip install --upgrade pip
RUN pip install poetry
RUN pip install pytest

COPY pyproject.toml $PROJECT_ROOT
COPY *.lock $PROJECT_ROOT

RUN poetry config virtualenvs.create false
RUN poetry update && poetry install --no-root --with dev

COPY . $PROJECT_ROOT

RUN PATH="$PROJECT_ROOT/bin:$PATH"
RUN PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"