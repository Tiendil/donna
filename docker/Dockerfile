FROM python:3.12

RUN pip install poetry

ARG UID=1000
ARG GID=1000
ARG USER=donna

RUN groupadd --gid $GID $USER && useradd --create-home --uid $UID --gid $USER --shell /bin/bash $USER

USER $USER

WORKDIR /repository

COPY README.md pyproject.toml poetry.lock* ./
COPY donna/__init__.py donna/

RUN poetry install --no-interaction --no-ansi

USER $USER

CMD []
