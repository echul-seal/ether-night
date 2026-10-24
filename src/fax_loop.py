#!/usr/bin/env python3
# Ether fax loop: every few minutes, scan the last 50 min of each fax station's audio for
# APT start (300 Hz) / stop (450 Hz) tones and decode every complete chart with fax.py.
import os, glob, json, time, re, calendar, subprocess, sys
import numpy as np
from PIL import Image
from scipy.io import wavfile
sys.path.insert(0, os.path.expanduser('~/ether/src'))
import fax
H = os.path.expanduser('~/ether')
ST = json.load(open(H + '/src/fax_stations.json'))
SCHED = json.load(open(H + '/src/jmh_schedule.json'))
DB = H + '/data/fax.json'
FS = 12000
WIN = 3000
for d in ['/site/fax', '/site/audio', '/data/fax_full', '/data/fax_rejects']:
    os.makedirs(H + d, exist_ok=True)

def load_db():
    return json.load(open(DB)) if os.path.exists(DB) else []

def fstart(p):
    m = re.search(r'(\d{8}T\d{6})Z', p)
    return calendar.timegm(time.strptime(m.group(1), '%Y%m%dT%H%M%S'))

def window(tag, now):
    t0 = now - WIN
    buf = np.zeros(WIN * FS, dtype=np.float32)
    have = np.zeros(WIN * FS, dtype=bool)
    for p in sorted(glob.glob(H + '/rec/' + tag + '/*.wav')):
        s = fstart(p)
        if s > now:
            continue
        x = np.fromfile(p, dtype=np.int16, offset=44).astype(np.float32)
        if s + len(x) / FS < t0:
            continue
        i0 = int(round((s - t0) * FS))
        a = max(0, -i0); b = min(len(x), WIN * FS - i0)
        if b <= a:
            continue
        buf[i0 + a:i0 + b] = x[a:b]; have[i0 + a:i0 + b] = True
    return t0, buf, have

def runs(x, th, minlen):
    out = []; i = 0; n = len(x)
    while i < n:
        if x[i] > th:
            j = i
            while j < n and x[j] > th:
                j += 1
            if j - i >= minlen:
                out.append((i, j))
            i = j
        else:
            i += 1
    return out

def label(tag, ts):
    if ST[tag].get('sched') != 'jmh':
        return ''
    tm = time.gmtime(ts); mins = tm.tm_hour * 60 + tm.tm_min + tm.tm_sec / 60.0
    best = ''; bd = 5
    for k, v in SCHED.items():
        d = abs(((int(k[:2]) * 60 + int(k[3:])) - mins + 720) % 1440 - 720)
        if d < bd:
            bd = d; best = v
    return best

def render(gs):
    width = int(round(np.pi * 576))
    p = fax.best_slant(gs, FS, 120, width)
    im = fax.slice_lines(gs, FS, 120, width, p)
    prof = im.mean(0); w = width // 20
    sm = np.convolve(np.concatenate([prof[-w:], prof, prof[:w]]), np.ones(w) / w, 'same')[w:-w]
    c = int(np.argmin(sm)); im = np.roll(im, -(c - w // 2), axis=1)
    lo, hi = np.percentile(im, 1), np.percentile(im, 99)
    return np.clip((im - lo) / (hi - lo + 1e-9), 0, 1), float(p)

def quality(im):
    cs = [np.corrcoef(im[k], im[k + 1])[0, 1] for k in range(0, len(im) - 1, 3)]
    c = float(np.nanmean(cs)) if cs else 0.0
    mid = float(np.mean((im > 0.25) & (im < 0.75)))
    return c, mid

def save(key, im, status):
    img = Image.fromarray((im * 255).astype(np.uint8))
    if status == 'chart':
        img.save(H + '/data/fax_full/' + key + '.png', optimize=True)
        t = img.resize((1000, max(1, int(img.height * 1000 / img.width))), Image.LANCZOS)
        t.save(H + '/site/fax/' + key + '.jpg', quality=85)
    else:
        img.resize((600, max(1, int(img.height * 600 / img.width)))).save(H + '/data/fax_rejects/' + key + '.jpg', quality=60)

def snippet(key, x, i):
    sa = max(0, int((i - 1) * FS)); sb = min(len(x), sa + 26 * FS)
    wavfile.write('/tmp/snip.wav', FS, np.clip(x[sa:sb], -32767, 32767).astype(np.int16))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', '/tmp/snip.wav', '-b:a', '48k', H + '/site/audio/' + key + '.mp3'])

def process(tag, now, db):
    st = ST[tag]
    t0, x, have = window(tag, now)
    if have.sum() < FS * 120:
        return
    g, d, amp = fax.demod(x, FS)
    s = fax.tone_track(d, FS, 300.0); e = fax.tone_track(d, FS, 450.0)
    starts = runs(s, 0.25, 3); stops = runs(e, 0.25, 3)
    with open(H + '/data/fax_events.log', 'a') as f:
        f.write('%s %s starts=%s stops=%s\n' % (time.strftime('%H:%M:%S', time.gmtime(now)), tag, [time.strftime('%H:%M:%S', time.gmtime(t0 + a)) for a, b in starts], [time.strftime('%H:%M:%S', time.gmtime(t0 + a)) for a, b in stops]))
    for (i, j) in starts:
        if i == 0:
            continue
        ts = t0 + i
        if any(r['tag'] == tag and abs(r['t_start'] - ts) < 60 for r in db):
            continue
        cands = [a for a, b in stops if a > j + 60] + [a for a, b in starts if a > j + 60]
        complete = bool([a for a, b in stops if a > j + 60])
        if cands:
            end = min(cands)
        else:
            if now - ts < 25 * 60:
                continue
            end = min(len(s), j + 22 * 60)
        a = (j + 30) * FS; b = end * FS
        if b - a < 60 * FS:
            continue
        im, ppm = render(g[a:b])
        c, mid = quality(im)
        lab = label(tag, ts)
        if 'SATELLITE' in lab:
            status = 'excluded_satellite'
        elif st.get('sched') == 'jmh':
            status = 'chart' if c > 0.3 else 'noise'
        else:
            status = 'chart' if (c > 0.3 and mid < 0.45) else ('excluded_photo' if c > 0.5 else 'noise')
        key = tag + '_' + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(ts))
        save(key, im, status)
        if status == 'chart':
            snippet(key, x, i)
        db.append(dict(key=key, tag=tag, t_start=ts, utc=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts)), t_end=t0 + end, minutes=round((end - i) / 60.0, 1), complete=complete, status=status, label=lab, corr=round(c, 3), midgray=round(mid, 3), ppm=ppm, lines=int(im.shape[0]), freq_khz=st['freq'], call=st['call'], tx=st['tx'], rx=st['rx'], rx_host=st['host']))

if __name__ == '__main__':
    while True:
        now = int(time.time())
        db = load_db()
        for tag in ST:
            try:
                process(tag, now, db)
            except Exception as ex:
                open(H + '/data/fax_errors.log', 'a').write('%s %s %r\n' % (time.ctime(), tag, ex))
            json.dump(db, open(DB, 'w'), indent=1)
        time.sleep(240)
