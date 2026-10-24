#!/bin/bash
# wait.sh ID SECONDS: serves wait/ID.json as waiting, flips to done after SECONDS (lets the agent pause between checks)
echo '{"status":"waiting"}' > ~/ether/wait/$1.json; sleep $2; echo '{"status":"done","utc":"'$(date -u +%H:%M)'"}' > ~/ether/wait/$1.json
