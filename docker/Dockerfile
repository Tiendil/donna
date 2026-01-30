FROM python:3.12

RUN pip install poetry

ARG UID=1000
ARG GID=1000
ARG USER=donna

RUN groupadd --gid $GID $USER && useradd --create-home --uid $UID --gid $USER --shell /bin/bash $USER

USER $USER

WORKDIR /repository

COPY donna/pyproject.toml donna/poetry.lock* ./
COPY README.md ./

RUN poetry install --no-interaction --no-ansi

USER $USER

CMD []
