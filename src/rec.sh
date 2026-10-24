#!/bin/bash
# rec.sh HOST PORT DIAL_KHZ TAG DT_SEC END_EPOCH
# Keeps a KiwiSDR USB recording alive (auto-reconnect) until END_EPOCH, splitting files on UTC boundaries every DT_SEC.
H=$1; P=$2; F=$3; T=$4; DT=$5; END=$6; shift 6
D=$HOME/ether/rec/$T; mkdir -p $D
while [ $(date +%s) -lt $END ]; do
  REM=$(( END - $(date +%s) ))
  timeout $REM python3 $HOME/kiwiclient/kiwirecorder.py -s $H -p $P -f $F -m usb -L 100 -H 3000 --dt-sec=$DT -d $D --station=$T --user=Seal-Ether -q "$@" >> $D/rec.log 2>&1
  echo "$(date -u +%FT%TZ) recorder exited $?" >> $D/rec.log
  sleep 30
done
