#!/usr/bin/env python3
"""Seal / Ether -- HF radiofax (WEFAX) decoder written from scratch.

Input: one or more consecutive USB audio WAVs recorded from a KiwiSDR with the
dial set 1.9 kHz below the assigned frequency (so the fax subcarrier sits at
1900 Hz audio: 1500 Hz = black, 2300 Hz = white).

Pipeline: complex mix to baseband -> lowpass -> FM discriminator -> grey level
-> APT start/stop tone detection (300 Hz / 450 Hz toggling) -> line slicing at
LPM with automatic sample-clock slant correction -> phasing alignment -> PNG.
"""
import sys, wave, json, argparse, os
import numpy as np
from scipy import signal
from PIL import Image

def read_wavs(paths):
    xs=[]; fs=None
    for p in paths:
        w=wave.open(p); fs=fs or w.getframerate()
        xs.append(np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32))
    return np.concatenate(xs), fs

def demod(x, fs, fc=1900.0, dev=400.0):
    n=np.arange(len(x)); z=x*np.exp(-2j*np.pi*fc*n/fs)
    b=signal.firwin(129, 1000.0, fs=fs); z=signal.lfilter(b,1,z)
    d=np.angle(z[1:]*np.conj(z[:-1]))*fs/(2*np.pi)
    d=np.concatenate([[0],d])
    amp=np.abs(z)
    g=np.clip((d+dev)/(2*dev),0,1)          # 0 = black (1500 Hz), 1 = white (2300 Hz)
    return g, d, amp

def tone_track(d, fs, f0, win=1.0):
    """power of an f0 Hz toggling component in the discriminator output, per window."""
    hop=int(fs*win); m=len(d)//hop
    b,a=signal.butter(2,[f0-25,f0+25],btype='band',fs=fs)
    y=signal.lfilter(b,a,d-np.mean(d))
    p=np.array([np.mean(y[i*hop:(i+1)*hop]**2) for i in range(m)])
    tot=np.array([np.var(d[i*hop:(i+1)*hop])+1e-9 for i in range(m)])
    return p/tot

def segments(d, fs, min_len=120):
    s=tone_track(d,fs,300.0); e=tone_track(d,fs,450.0)
    starts=[i for i in range(1,len(s)) if s[i]>0.25 and s[i-1]<=0.25]
    stops=[i for i in range(1,len(e)) if e[i]>0.25 and e[i-1]<=0.25]
    segs=[]
    for st in starts:
        nxt=[x for x in stops if x>st+min_len]
        en=nxt[0] if nxt else len(s)
        if not segs or st>segs[-1][1]: segs.append((st,en))
    return segs, s, e

def slice_lines(g, fs, lpm, width, ppm, off=0):
    spl=fs*60.0/lpm*(1+ppm*1e-6)
    nl=int((len(g)-off)/spl)-1
    if nl<10: return None
    t=off+np.arange(nl)[:,None]*spl+np.arange(width)[None,:]*spl/width
    i=t.astype(np.int64); f=t-i
    return g[i]*(1-f)+g[np.minimum(i+1,len(g)-1)]*f

def best_slant(g, fs, lpm, width, rng=400, step=2):
    # downsampled search: vertical structures align when the clock is right
    best=(0,-1)
    for ppm in np.arange(-rng,rng+step,step):
        im=slice_lines(g,fs,lpm,width//4,ppm)
        if im is None: return 0
        sc=np.var(im.mean(0))
        if sc>best[1]: best=(ppm,sc)
    # refine
    b0=best[0]
    for ppm in np.arange(b0-step,b0+step,0.25):
        im=slice_lines(g,fs,lpm,width//4,ppm); sc=np.var(im.mean(0))
        if sc>best[1]: best=(ppm,sc)
    return best[0]

def phase_align(im, nphase=40):
    # phasing lines: mostly white with a black pulse (or inverse) at line start
    prof=im[:nphase].mean(0)
    k=np.ones(max(3,im.shape[1]//40))/max(3,im.shape[1]//40)
    sm=np.convolve(np.concatenate([prof,prof]),k,'same')[:len(prof)]
    col=int(np.argmin(sm)) if (prof.max()-prof.min())>0.2 else 0
    return np.roll(im,-col,axis=1), col

def decode(paths, out, lpm=120, ioc=576, ppm=None, label=''):
    x,fs=read_wavs(paths)
    g,d,amp=demod(x,fs)
    segs,s,e=segments(d,fs)
    width=int(round(np.pi*ioc))
    results=[]
    if not segs: segs=[(0,len(d)//fs)]
    for k,(st,en) in enumerate(segs):
        a=int(st*fs); b=int(min(en*fs,len(g)))
        gs=g[a:b]
        if len(gs)<fs*60: continue
        p=ppm if ppm is not None else best_slant(gs,fs,lpm,width)
        im=slice_lines(gs,fs,lpm,width,p)
        im,col=phase_align(im)
        # skip the start tone + phasing block (~40 s = 80 lines at 120 lpm)
        body=im[int(40*lpm/60):]
        lo,hi=np.percentile(body,1),np.percentile(body,99)
        body=np.clip((body-lo)/(hi-lo+1e-9),0,1)
        fn=f"{out}_{k}.png"
        Image.fromarray((body*255).astype(np.uint8)).save(fn)
        snr=float(20*np.log10(np.median(amp[a:b])/(np.median(amp)+1e-9)+1e-9))
        results.append(dict(file=fn,start_s=st,end_s=en,lines=int(body.shape[0]),ppm=float(p),phase_col=col,label=label))
    return results, segs

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('wavs',nargs='+'); ap.add_argument('-o',default='fax')
    ap.add_argument('--lpm',type=float,default=120); ap.add_argument('--ioc',type=int,default=576); ap.add_argument('--ppm',type=float)
    a=ap.parse_args()
    r,segs=decode(a.wavs,a.o,a.lpm,a.ioc,a.ppm)
    print(json.dumps(dict(segments=segs,results=r),indent=1))
