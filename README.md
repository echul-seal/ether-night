# Ether: one night of the planet's radio

On the night of 24 to 25 October 2026 (UTC) Seal borrowed public KiwiSDR shortwave receivers on every continent, streamed them to rented machines, and decoded what was in the air: HF radiofax weather charts (decoder written from scratch, `src/fax.py`, `src/fax_loop.py`) and FT8/WSPR digital-mode signals (WSJT-X `jt9` / `wsprd`, `src/digi_loop.py`). No satellite content.

- Live page: https://echul-seal.github.io/ether-night/
- `src/`: decoders, recorders, page builder, sync and end-of-night scripts
- `data/fax/`: fax log and full-resolution charts; `data/vision.json`: the eye check every gallery chart passed; `data/ipfs.json`: permanent IPFS copies
- `data/digi/`: every FT8/WSPR decode (gzip JSONL), per box
- `SOURCE.md`: notes from the first hours

Tags: `v1` first charts + rescued source; `v2` the finished night log.
