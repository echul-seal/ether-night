#!/bin/bash
# End of night (00:02 UTC): stop recorders, final merge+build, commit, tag v2, then delete every Ether machine.
until [ $(date +%s) -ge $(date -d '2026-10-25 00:02 UTC' +%s) ]; do sleep 30; done
cd ~/ether
i=0; for u in $(cat src/digi_boxes.txt); do i=$((i+1)); curl -s -m 120 $u/data/decodes.jsonl -o data/dec_$i.new && [ -s data/dec_$i.new ] && mv data/dec_$i.new data/dec_$i.jsonl; done
cat data/dec_*.jsonl > data/decodes.jsonl
sleep 240
python3 src/analyze_digi.py data/decodes.jsonl data/digi_summary.json > data/analyze.log 2>&1
python3 src/build_site.py >> data/analyze.log 2>&1
pkill -f sync_all.sh
cd ~/ether-night && git pull -q --rebase origin main
rsync -a --delete --exclude .git --exclude src --exclude data --exclude README.md --exclude SOURCE.md ~/ether/site/ ~/ether-night/
cp ~/ether/src/*.py ~/ether/src/*.sh ~/ether/src/*.json ~/ether/src/*.txt src/ 2>/dev/null; cp ~/ether/data/fax.json ~/ether/data/fax_events.log ~/ether/data/vision.json ~/ether/data/ipfs.json ~/ether/data/digi_summary.json data/ 2>/dev/null; gzip -c ~/ether/data/decodes.jsonl > data/digi/decodes_all.jsonl.gz
git add -A; git commit -qm 'final: the night log of the ether, 00:06 UTC'; git push -q origin main
git tag -a v2 -m 'Ether v2: finished night log' && git push -q origin v2
echo "final done $(date -u)" >> ~/final.log
K=$(cat ~/.rpk)
for m in rp_vm_tp2h0byzq3 rp_vm_3l3d8w7uks rp_vm_51e7zzckwk rp_vm_5gucr5lxtt; do curl -s -m 20 -X DELETE -H "Authorization: Bearer $K" https://router.reachpad.dev/v1/machines/$m >> ~/final.log; done
