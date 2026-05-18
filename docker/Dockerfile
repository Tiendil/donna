FROM python:3.12

COPY --from=ghcr.io/astral-sh/uv:0.11.14 /uv /uvx /bin/

ARG UID=1000
ARG GID=1000
ARG USER=donna

RUN groupadd --gid $GID $USER && useradd --create-home --uid $UID --gid $USER --shell /bin/bash $USER

USER $USER

WORKDIR /repository

ENV UV_PROJECT_ENVIRONMENT=/home/donna/.venv
ENV UV_PYTHON_DOWNLOADS=never
ENV UV_LINK_MODE=copy
ENV PATH="/home/donna/.venv/bin:${PATH}"

COPY --chown=$USER:$USER . /repository

RUN uv sync --locked

ENV UV_NO_SYNC=1

CMD []
