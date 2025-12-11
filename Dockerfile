FROM debian:12 AS v8-base
ENV RAGENT_HOST ragent
ENV RAGENT_PORT 1540
ENV RAGENT_REGPORT 1541
ENV RAGENT_PORTRANGE 1560:1591
ENV RAS_PORT 1545
WORKDIR /distr
COPY /docker/1c-enterprise-*-common_*_amd64.deb common_amd64.deb
COPY /docker/1c-enterprise-*-server_*_amd64.deb server_amd64.deb
RUN dpkg -i common_amd64.deb && dpkg -i server_amd64.deb && rm *.deb
WORKDIR /opt/1cv8

FROM v8-base AS ragent
ENV RAGENT_HOME /home/1c/ragent
RUN mkdir -p ${RAGENT_HOME}/reg_${RAGENT_REGPORT}
COPY docker/ragent-entrypoint.sh /opt/docker/entrypoint.sh
RUN chmod +x /opt/docker/entrypoint.sh
ENTRYPOINT ["/opt/docker/entrypoint.sh"]

FROM v8-base AS ras
COPY docker/ras-entrypoint.sh /opt/docker/entrypoint.sh
RUN chmod +x /opt/docker/entrypoint.sh
ENTRYPOINT ["/opt/docker/entrypoint.sh"]

FROM python:3.13 AS python-base
ENV PYTHONUNBUFFERED 1
ENV POETRY_VERSION=1.8.4
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

FROM python-base AS poetry-base
RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip install -U pip setuptools \
    && $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

FROM python-base AS rac
COPY --from=ras /opt/1cv8 /opt/1cv8
COPY --from=poetry-base ${POETRY_VENV} ${POETRY_VENV}
ENV PATH="${PATH}:${POETRY_VENV}/bin"
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry check \
    && poetry install --no-interaction --no-cache --no-root --without dev --with debug
COPY docker/rac-entrypoint.sh /opt/docker/entrypoint.sh
RUN chmod +x /opt/docker/entrypoint.sh
ENTRYPOINT ["/opt/docker/entrypoint.sh"]
