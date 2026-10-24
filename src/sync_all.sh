#!/bin/bash
# Every 10 min: mirror built page + source + data into echul-seal/ether-night (main) and push. Single repo.
cd ~/ether-night && git config user.name Seal && git config user.email seal@sealmails.com
while true; do
  cd ~/ether-night && git pull -q --rebase origin main >/dev/null 2>&1
  rsync -a --delete --exclude .git --exclude src --exclude data --exclude README.md --exclude SOURCE.md ~/ether/site/ ~/ether-night/
  mkdir -p src data/fax
  cp ~/ether/src/*.py ~/ether/src/*.sh ~/ether/src/*.json src/ 2>/dev/null
  cp ~/ether/data/fax.json ~/ether/data/fax_events.log data/fax/ 2>/dev/null
  cp ~/ether/data/fax_full/*.png data/fax/ 2>/dev/null
  [ -f ~/ether/data/ipfs.json ] && cp ~/ether/data/ipfs.json data/
  touch .nojekyll
  git add -A && git commit -qm "night log + fax data @ $(date -u +%H:%MZ)" && git push -q origin main >>~/push.log 2>&1 || echo "push fail $(date -u)" >>~/push.log
  find ~/ether/rec/fax_* -name '*.wav' -mmin +70 -delete
  sleep 600
done
