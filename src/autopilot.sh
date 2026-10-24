#!/bin/bash
# Every 10 min: pull digi decodes from every digi box (urls in src/digi_boxes.txt), merge, re-analyse, rebuild the page into site/.
cd ~/ether
while true; do
  i=0; for u in $(cat src/digi_boxes.txt); do i=$((i+1)); curl -s -m 90 $u/data/decodes.jsonl -o data/dec_$i.new && [ -s data/dec_$i.new ] && mv data/dec_$i.new data/dec_$i.jsonl; done
  cat data/dec_*.jsonl > data/decodes.jsonl 2>/dev/null
  python3 src/analyze_digi.py data/decodes.jsonl data/digi_summary.json > data/analyze.log 2>&1
  python3 src/build_site.py >> data/analyze.log 2>&1
  sleep 600
done
