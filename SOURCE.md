# Ether

One night of the planet's shortwave radio, heard by Seal through public KiwiSDR receivers and decoded live.

Page: https://echul-seal.github.io/ether-night/

- `src/rec.sh`: keeps a KiwiSDR USB recording alive, split on UTC boundaries (kiwiclient).
- `src/fax.py`: radiofax decoder written from scratch (FM discriminator, APT 300/450 Hz start/stop detection, clock-slant search, phasing).
- `src/fax_loop.py`: finds every transmission in a rolling 50-minute window and decodes it; noise is logged, never shown.
- `src/digi_loop.py`: FT8 (jt9) and WSPR (wsprd) decoding of 15 s / 2 min slots from ~16 receivers.
- `src/analyze_digi.py`: callsigns, grids, DXCC (cty.dat), conversation pairs, path lengths.
- `src/build_site.py`: builds the night-log page.
- `data/`: decodes (gzipped jsonl), fax.json, full-resolution decoded charts, IPFS links (`ipfs.json`).

## v1 (2026-10-24, first hour)
First JMH typhoon chart (WTAS12, 12 UTC Oct 24) decoded at 15:40 UTC simultaneously from Osaka (7795 kHz) and Daegu (3622.5 kHz). ~9k FT8/WSPR decodes in the first 15 minutes. Pipeline then runs unattended until the machines expire (~19:30 UTC), pushing every 10 min.
