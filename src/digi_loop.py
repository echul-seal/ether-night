#!/usr/bin/env python3
"""Watches ~/ether/rec/<tag>/ for finished 15 s (FT8) / 120 s (WSPR) slot files, decodes them with
WSJT-X's jt9 (FT8) or wsprd (WSPR), appends every decode to data/decodes.jsonl, and deletes the audio.
One random slot per channel per hour is kept as an audio souvenir in rec/keep/."""
import os, glob, time, json, subprocess, shutil, struct, re, tempfile, random
HOME=os.path.expanduser('~/ether'); OUT=HOME+'/data/decodes.jsonl'
CH=json.load(open(HOME+'/src/channels.json'))
os.makedirs(HOME+'/rec/keep',exist_ok=True)
def fix_rate(p):
    with open(p,'r+b') as f:
        f.seek(24); f.write(struct.pack('<I',12000)); f.seek(28); f.write(struct.pack('<I',24000))
def ft8(p,tmp):
    r=subprocess.run(['jt9','-8','-d','3','-a',tmp,'-t',tmp,p],capture_output=True,text=True,timeout=60,cwd=tmp)
    out=[]
    for l in r.stdout.splitlines():
        m=re.match(r'^(\d{6})\s+(-?\d+)\s+(-?[\d.]+)\s+(\d+)\s+~\s+(.*?)\s*$',l)
        if m: out.append(dict(snr=int(m[2]),dt=float(m[3]),df=int(m[4]),msg=m[5].strip()))
    return out
def wspr(p,tmp,dial):
    r=subprocess.run(['wsprd','-f','%.6f'%(dial/1000.0),'-a',tmp,p],capture_output=True,text=True,timeout=110,cwd=tmp)
    out=[]
    for l in r.stdout.splitlines():
        s=l.split()
        if len(s)>=6 and not l.startswith('<'):
            try: out.append(dict(snr=int(s[1]),dt=float(s[2]),freq_mhz=float(s[3]),drift=int(s[4]),msg=' '.join(s[5:])))
            except: pass
    return out
seen=set(); hourkeep={}
from concurrent.futures import ThreadPoolExecutor
POOL=ThreadPoolExecutor(24)
def job(tag,c,p,ts,sz):
    need=12000*2*(13 if c['mode']=='ft8' else 110)
    res=[]
    if sz>=need:
        tmp=tempfile.mkdtemp()
        try:
            fix_rate(p)
            res=ft8(p,tmp) if c['mode']=='ft8' else wspr(p,tmp,c['dial'])
        except Exception as e: open(HOME+'/data/errors.log','a').write(f'{p} {e}\n')
        shutil.rmtree(tmp,ignore_errors=True)
    with open(OUT,'a') as f:
        for d in res:
            d.update(rx=tag,host=c['host'],rx_loc=c['loc'],rx_lat=c['lat'],rx_lon=c['lon'],dial_khz=c['dial'],mode=c['mode'],utc=ts)
            f.write(json.dumps(d)+'\n')
    with open(HOME+'/data/slots.log','a') as f: f.write(f'{tag} {ts} {sz} {len(res)}\n')
    hk=(tag,ts[:11])
    if len(res)>=5 and hk not in hourkeep:
        hourkeep[hk]=1; shutil.copy(p,f'{HOME}/rec/keep/{tag}_{ts}.wav')
    try: os.remove(p)
    except: pass

while True:
    now=time.time()
    for tag,c in CH.items():
        for p in sorted(glob.glob(f'{HOME}/rec/{tag}/*.wav')):
            if now-os.path.getmtime(p)<4 or p in seen: continue
            seen.add(p)
            m=re.search(r'(\d{8}T\d{6})Z',p); ts=m[1] if m else ''
            POOL.submit(job,tag,c,p,ts,os.path.getsize(p))
    time.sleep(3)
