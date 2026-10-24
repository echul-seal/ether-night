#!/bin/bash
# Every 10 min: pull latest digi decodes from the digi box, re-analyse, rebuild the page into site/ (served + committed by sync_fax.sh).
while true; do
  curl -s -m 60 https://8080-0woi0gabk8ioh1yv.daytonaproxy01.net/data/decodes.jsonl -o data/decodes.jsonl.new && [ -s data/decodes.jsonl.new ] && mv data/decodes.jsonl.new data/decodes.jsonl
  python3 src/analyze_digi.py data/decodes.jsonl data/digi_summary.json > data/analyze.log 2>&1
  python3 src/build_site.py >> data/analyze.log 2>&1
  cp data/digi_summary.json ~/ether_git/data/ 2>/dev/null; cp src/analyze_digi.py src/build_site.py src/notes.json src/autopilot.sh ~/ether_git/src/ 2>/dev/null; cp site/index.html ~/ether_git/site/ 2>/dev/null
  sleep 600
done
