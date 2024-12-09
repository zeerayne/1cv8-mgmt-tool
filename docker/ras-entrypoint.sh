#!/bin/sh
set -e

export PATH="$PATH:/opt/1cv8/x86_64/$(ls /opt/1cv8/x86_64)"

echo "IP: `awk 'END{print $1}' /etc/hosts`"
echo "PATH: $PATH"
echo "RAS_PORT: $RAS_PORT"
echo "RAGENT_HOST: $RAGENT_HOST"
echo "RAGENT_PORT: $RAGENT_PORT"

ras cluster --port $RAS_PORT $RAGENT_HOST:$RAGENT_PORT
