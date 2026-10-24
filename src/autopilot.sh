#!/bin/bash
# Every 10 min: pull latest digi decodes from the digi box, re-analyse, rebuild the page into site/ (served + committed by sync_fax.sh).
while true; do
  curl -s -m 60 https://8080-0woi0gabk8ioh1yv.daytonaproxy01.net/data/decodes.jsonl -o data/decodes.jsonl.new && [ -s data/decodes.jsonl.new ] && mv data/decodes.jsonl.new data/decodes.jsonl
  python3 src/analyze_digi.py data/decodes.jsonl data/digi_summary.json > data/analyze.log 2>&1
  python3 src/build_site.py >> data/analyze.log 2>&1
  true
  sleep 600
done
