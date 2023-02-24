#!/bin/bash
export PATH="$PATH:/opt/1cv8/x86_64/$(ls /opt/1cv8/x86_64)"
export RAGENT_WORKDIR="$RAGENT_HOME/reg_$RAGENT_REGPORT"

echo "IP: `awk 'END{print $1}' /etc/hosts`"
echo "PATH: $PATH"
echo "RAGENT_HOME: $RAGENT_HOME"
echo "RAGENT_PORT: $RAGENT_PORT"
echo "RAGENT_REGPORT: $RAGENT_REGPORT"
echo "RAGENT_PORTRANGE: $RAGENT_PORTRANGE"

sync() {
    if [[ -n "${RAGENT_VOLUME}" ]]; then
        echo "Syncing configuration from $RAGENT_VOLUME to $RAGENT_HOME"
        cp -f "$RAGENT_VOLUME/1cv8wsrv.lst" "$RAGENT_HOME/1cv8wsrv.lst"
        cp -f "$RAGENT_VOLUME/rescntsrv.lst" "$RAGENT_WORKDIR/rescntsrv.lst"
        cp -f "$RAGENT_VOLUME/1CV8Clst.lst" "$RAGENT_WORKDIR/1CV8Clst.lst"
        echo "Sync completed"
    else
        echo "RAGENT_VOLUME variable is not set, configuration will not be persisted"
    fi
}

sync_reverse() {
    if [[ -n "${RAGENT_VOLUME}" ]]; then
        echo "Syncing configuration from $RAGENT_HOME to $RAGENT_VOLUME"
        cp -f "$RAGENT_HOME/1cv8wsrv.lst" "$RAGENT_VOLUME/1cv8wsrv.lst"
        cp -f "$RAGENT_WORKDIR/rescntsrv.lst" "$RAGENT_VOLUME/rescntsrv.lst"
        cp -f "$RAGENT_WORKDIR/1CV8Clst.lst" "$RAGENT_VOLUME/1CV8Clst.lst"
        echo "Sync completed"
    fi
}

sync

trap 'sync_reverse' SIGTERM

echo "Starting ragent"

ragent -port $RAGENT_PORT -regport $RAGENT_REGPORT -range $RAGENT_PORTRANGE -d $RAGENT_HOME &

wait $!
