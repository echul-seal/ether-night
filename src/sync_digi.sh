#!/bin/bash
# Every 10 min: copy digital-mode decodes + source into ether-night (data/digi, src) and push.
cd ~/ether-night && git config user.name Seal && git config user.email seal@sealmails.com
while true; do
  cd ~/ether-night && git pull -q --rebase origin main >/dev/null 2>&1
  mkdir -p data/digi src
  gzip -c ~/ether/data/decodes.jsonl > data/digi/decodes_b.jsonl.gz
  gzip -c ~/ether/data/slots.log > data/digi/slots_b.log.gz
  cp ~/ether/src/channels.json src/channels_b.json; cp ~/ether/src/digi_loop.py ~/ether/src/rec.sh ~/ether/src/sync_digi.sh src/ 2>/dev/null
  git add -A && git commit -qm "digi: $(wc -l < ~/ether/data/decodes.jsonl) decodes @ $(date -u +%H:%MZ)"
  for i in 1 2 3; do git push -q origin main >>~/push.log 2>&1 && break; git pull -q --rebase origin main; done
  sleep 600
done
