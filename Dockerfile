FROM ubuntu:jammy
WORKDIR /distr
COPY server64.tar.gz server64.tar.gz
RUN tar xzf server64.tar.gz
RUN ./setup-*.run \
    --mode unattended \
    --enable-components server,server_admin,additional_admin_functions,liberica_jre,ru \
    --installer-language en && \
    rm -rf /distr
RUN mkdir /home/1c
WORKDIR /opt/1cv8
CMD ./x86_64/8.*/ras cluster --port 1545 --daemon localhost:1540 && \
    ./x86_64/8.*/ragent -port 1540 -regport 1541 -range 1560:1591 -d /home/1c
