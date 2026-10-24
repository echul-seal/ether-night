#!/bin/bash
# Every 10 min: mirror the built page (site/) to the public ether-night repo (GitHub Pages) and prune old fax audio.
cd ~/ether-night && git config user.name Seal && git config user.email seal@sealmails.com
while true; do
  cd ~/ether-night && git checkout -q main 2>/dev/null || git checkout -q -b main
  rsync -a --delete --exclude .git ~/ether/site/ ~/ether-night/ 2>/dev/null || cp -r ~/ether/site/* ~/ether-night/
  touch .nojekyll
  git add -A && git commit -qm "night log @ $(date -u +%H:%MZ)" && git push -q -u origin main >/dev/null 2>&1
  # keep only the last 70 min of raw fax audio on disk
  find ~/ether/rec/fax_* -name '*.wav' -mmin +70 -delete
  sleep 600
done
