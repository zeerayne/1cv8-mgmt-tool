FROM ubuntu:jammy AS v8-base
ENV RAGENT_HOST ragent
ENV RAGENT_PORT 1540
ENV RAGENT_REGPORT 1541
ENV RAGENT_PORTRANGE 1560:1591
ENV RAS_PORT 1545
WORKDIR /distr
COPY server64.tar.gz server64.tar.gz
RUN tar xzf server64.tar.gz \
    && rm server64.tar.gz
WORKDIR /opt/1cv8

FROM v8-base AS ragent
RUN /distr/setup-*.run \
    --mode unattended \
    --enable-components server,liberica_jre,ru \
    --installer-language en \
    && rm -rf /distr
RUN mkdir /home/1c
CMD printf RAGENT_PORT=$RAGENT_PORT'\n'RAGENT_REGPORT=$RAGENT_REGPORT'\n'RAGENT_PORTRANGE=$RAGENT_PORTRANGE'\n' \
    && ./x86_64/8.*/ragent -port $RAGENT_PORT -regport $RAGENT_REGPORT -range $RAGENT_PORTRANGE -d /home/1c

FROM v8-base AS ras
RUN /distr/setup-*.run \
    --mode unattended \
    --enable-components server_admin,liberica_jre,ru \
    --installer-language en \
    && rm -rf /distr
CMD printf RAS_PORT=$RAS_PORT'\n'RAGENT_HOST=$RAGENT_HOST'\n'RAGENT_PORT=$RAGENT_PORT'\n' \
    && ./x86_64/8.*/ras cluster --port $RAS_PORT $RAGENT_HOST:$RAGENT_PORT

FROM python:3.10 as python-base
ENV POETRY_VERSION=1.3.2
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

FROM python-base as poetry-base
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
