#!/usr/bin/env python3
"""Ether: turn raw FT8/WSPR decodes into a contact graph.
Parses each message into callsigns + Maidenhead grid, locates stations (grid if ever heard, else
DXCC prefix centroid from cty.dat), builds QSO pairs ("A B ..." = B calling A), and the
heard-by links (transmitter -> receiving KiwiSDR). Writes data/digi_summary.json."""
import json, re, math, sys, collections, os
H=os.path.expanduser('~/ether')
CALL=re.compile(r'^(?=.*\d)(?=.*[A-Z])[A-Z0-9]{1,3}[0-9][A-Z0-9]{0,4}(/[A-Z0-9]{1,4})?$|^[A-Z0-9]{1,4}/(?=.*\d)[A-Z0-9]{3,8}$')
GRID=re.compile(r'^[A-R]{2}[0-9]{2}([a-x]{2})?$')
def g2ll(g):
    lon=(ord(g[0])-65)*20-180+int(g[2])*2+1; lat=(ord(g[1])-65)*10-90+int(g[3])+0.5
    return lat,lon
def load_cty(p):
    ents=[]; pref={}; exact={}
    txt=open(p,encoding='latin-1').read().replace('\r','')
    for blk in txt.split(';'):
        blk=blk.strip()
        if not blk: continue
        head,_,body=blk.partition('\n') if blk.count(':')<8 else (blk,'','')
        parts=blk.split(':')
        if len(parts)<9: continue
        name=parts[0].strip(); lat=float(parts[4]); lon=-float(parts[5]); cont=parts[3].strip()
        e=(name,lat,lon,cont)
        items=[parts[7].strip()]+[x.strip() for x in parts[8].replace('\n','').split(',')]
        for it in items:
            if not it: continue
            ov=re.search(r'<([-\d.]+)/([-\d.]+)>',it)
            ee=(name,float(ov[1]),-float(ov[2]),cont) if ov else e
            k=re.sub(r'[\(\[<{~].*$','',it).lstrip('*')
            if k.startswith('='): exact[k[1:]]=ee
            elif k: pref[k]=ee
    return pref,exact
PREF,EXACT=load_cty(H+'/data/ref/cty.dat')
def dxcc(c):
    if c in EXACT: return EXACT[c]
    base=c
    if '/' in c:
        a,b=c.split('/',1); base=a if len(a)<=len(b) and not b.isdigit() and len(a)<4 else (b if len(b)>len(a) else a)
        if b in ('P','M','MM','QRP','AM') or b.isdigit(): base=a
    for n in range(len(base),0,-1):
        if base[:n] in PREF: return PREF[base[:n]]
    return None
def parse(msg,mode):
    t=msg.replace('<','').replace('>','').split()
    if mode=='wspr':
        if len(t)>=2 and CALL.match(t[0]) and GRID.match(t[1][:4] if len(t[1])>=4 else 'x'):
            return t[0],None,t[1][:4]
        return None
    if not t: return None
    if t[0]=='CQ':
        r=t[1:]
        if r and not CALL.match(r[0]) and len(r)>1: r=r[1:]
        if r and CALL.match(r[0]):
            g=r[1] if len(r)>1 and GRID.match(r[1]) and r[1]!='RR73' else None
            return r[0],None,g
        return None
    if len(t)>=2 and CALL.match(t[0]) and CALL.match(t[1]):
        g=t[2] if len(t)>2 and GRID.match(t[2]) and t[2]!='RR73' else None
        return t[1],t[0],g
    return None
def hav(a,b):
    la1,lo1,la2,lo2=map(math.radians,(a[0],a[1],b[0],b[1]))
    return 6371*2*math.asin(math.sqrt(math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2))
def main():
    rows=[json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    grid={}; heard=collections.defaultdict(list); qso=collections.Counter(); cq=collections.Counter()
    per_hour=collections.Counter(); per_rx=collections.Counter(); rx={}
    parsed=[]
    for r in rows:
        p=parse(r['msg'],r['mode'])
        rx[r['rx']]=dict(loc=r['rx_loc'],lat=r.get('rx_lat'),lon=r.get('rx_lon'),dial=r['dial_khz'],mode=r['mode'])
        per_rx[r['rx']]+=1; per_hour[(r['utc'][9:11],r['rx'])]+=1
        if not p: continue
        frm,to,g=p
        if g: grid[frm]=g
        parsed.append((r,frm,to))
        if to: qso[tuple(sorted((frm,to)))]+=1
        elif r['msg'].startswith('CQ'): cq[frm]+=1
    def loc(c):
        if c in grid: return g2ll(grid[c])+('grid',)
        d=dxcc(c)
        return (d[1],d[2],'dxcc') if d else None
    stations={}
    for r,frm,to in parsed:
        for c in (frm,to):
            if c and c not in stations:
                l=loc(c); d=dxcc(c)
                if l: stations[c]=dict(lat=round(l[0],2),lon=round(l[1],2),how=l[2],country=d[0] if d else '?',cont=d[3] if d else '?',grid=grid.get(c,''))
        if frm in stations and r.get('rx_lat') is not None:
            heard[frm].append((r['rx'],r['snr'],r['utc']))
    links=[]; best=[]
    for c,hs in heard.items():
        s=stations[c]
        for rxk in set(h[0] for h in hs):
            R=rx[rxk]; dist=hav((s['lat'],s['lon']),(R['lat'],R['lon']))
            sn=max(h[1] for h in hs if h[0]==rxk)
            links.append(dict(tx=c,rx=rxk,km=round(dist),snr=sn,precise=s['how']=='grid'))
    links.sort(key=lambda x:-x['km'])
    q=[dict(a=a,b=b,n=n) for (a,b),n in qso.items() if a in stations and b in stations]
    for x in q: x['km']=round(hav((stations[x['a']]['lat'],stations[x['a']]['lon']),(stations[x['b']]['lat'],stations[x['b']]['lon'])))
    countries=collections.Counter(s['country'] for s in stations.values())
    out=dict(n_decodes=len(rows),n_ft8=sum(r['mode']=='ft8' for r in rows),n_wspr=sum(r['mode']=='wspr' for r in rows),
      first_utc=min(r['utc'] for r in rows),last_utc=max(r['utc'] for r in rows),
      n_stations=len(stations),n_countries=len(countries),n_qso=len(q),receivers=rx,per_rx=per_rx,
      per_hour={f'{h}|{k}':v for (h,k),v in per_hour.items()},stations=stations,qsos=q,links=links,
      top_countries=countries.most_common(40),longest=[l for l in links if l['precise']][:15],
      top_cq=cq.most_common(20))
    json.dump(out,open(sys.argv[2],'w'))
    print(json.dumps({k:out[k] for k in ['n_decodes','n_ft8','n_wspr','first_utc','last_utc','n_stations','n_countries','n_qso']}))
    print('longest:',[(l['tx'],stations[l['tx']]['country'],l['rx'],l['km'],l['snr']) for l in out['longest'][:8]])
    print('countries:',out['top_countries'][:15])
main()
