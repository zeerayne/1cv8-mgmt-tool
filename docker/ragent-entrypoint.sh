#!/bin/sh
set -e

export PATH="$PATH:/opt/1cv8/x86_64/$(ls /opt/1cv8/x86_64)"

echo "IP: `awk 'END{print $1}' /etc/hosts`"
echo "PATH: $PATH"
echo "RAGENT_PORT: $RAGENT_PORT"
echo "RAGENT_REGPORT: $RAGENT_REGPORT"
echo "RAGENT_PORTRANGE: $RAGENT_PORTRANGE"

ragent -port $RAGENT_PORT -regport $RAGENT_REGPORT -range $RAGENT_PORTRANGE -d /home/1c
