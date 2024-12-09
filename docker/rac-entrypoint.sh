#!/bin/sh
set -e

export PATH="$PATH:/opt/1cv8/x86_64/$(ls /opt/1cv8/x86_64)"

echo "IP: `awk 'END{print $1}' /etc/hosts`"
echo "PATH: $PATH"
echo "CMD: $@"

poetry run python -m debugpy --wait-for-client --listen 0.0.0.0:5678 $@
