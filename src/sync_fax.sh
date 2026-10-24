#!/bin/bash
# Every 10 min: copy fax decodes (chart PNGs, thumbnails, audio snippets, db) + source into git and push.
cd ~ && [ -d ether_git ] || git clone -q https://x-access-token:$GH@github.com/echul-seal/ether.git ether_git
cd ~/ether_git && git config user.name Seal && git config user.email seal@sealmails.com
while true; do
  cd ~/ether_git && git pull -q --rebase origin main >/dev/null 2>&1
  mkdir -p data/fax site/fax site/audio src
  cp ~/ether/data/fax.json ~/ether/data/fax_events.log data/fax/ 2>/dev/null
  cp ~/ether/data/fax_full/*.png data/fax/ 2>/dev/null
  cp ~/ether/site/fax/*.jpg site/fax/ 2>/dev/null
  cp ~/ether/site/audio/*.mp3 site/audio/ 2>/dev/null
  cp ~/ether/src/fax.py ~/ether/src/fax_loop.py ~/ether/src/fax_stations.json ~/ether/src/jmh_schedule.json src/
  git add -A && git commit -qm "fax: $(python3 -c "import json;d=json.load(open('$HOME/ether/data/fax.json'));print(sum(r['status']=='chart' for r in d),'charts of',len(d),'transmissions')" 2>/dev/null) @ $(date -u +%H:%MZ)" && git push -q origin main >/dev/null 2>&1
  sleep 600
done
