FROM ubuntu:jammy AS base
ENV RAGENT_HOST ragent
ENV RAGENT_PORT 1540
ENV RAGENT_REGPORT 1541
ENV RAGENT_PORTRANGE 1560:1591
ENV RAS_PORT 1545
WORKDIR /distr
COPY server64.tar.gz server64.tar.gz
RUN tar xzf server64.tar.gz

FROM base AS ragent
RUN ./setup-*.run \
    --mode unattended \
    --enable-components server,liberica_jre,ru \
    --installer-language en && \
    rm -rf /distr
RUN mkdir /home/1c
WORKDIR /opt/1cv8
CMD printf RAGENT_PORT=$RAGENT_PORT'\n'RAGENT_REGPORT=$RAGENT_REGPORT'\n'RAGENT_PORTRANGE=$RAGENT_PORTRANGE'\n' && \
    ./x86_64/8.*/ragent -port $RAGENT_PORT -regport $RAGENT_REGPORT -range $RAGENT_PORTRANGE -d /home/1c

FROM ragent AS ras
CMD printf RAS_PORT=$RAS_PORT'\n'RAGENT_HOST=$RAGENT_HOST'\n'RAGENT_PORT=$RAGENT_PORT'\n' && \
    ./x86_64/8.*/ras cluster --port $RAS_PORT $RAGENT_HOST:$RAGENT_PORT
