import json,re
s=open('kiwilist.js').read()
s=s[s.index('['):s.rindex(']')+1]
s=re.sub(r',\s*\]',']',s); s=re.sub(r',\s*}','}',s)
L=json.loads(s)
out=[]
for r in L:
  if r.get('offline')!='no' or r.get('status')!='active': continue
  try:
    lat,lon=[float(x) for x in r['gps'].strip('()').split(',')]
  except: continue
  out.append(dict(name=r['name'][:70],url=r['url'],lat=lat,lon=lon,users=int(r.get('users',0)),umax=int(r.get('users_max',0)),snr=r.get('snr',''),loc=r.get('loc','')[:40],bands=r.get('bands','')))
json.dump(out,open('kiwis.json','w'))
print(len(L),len(out))
import sys
for reg,(la0,la1,lo0,lo1) in {'japan':(24,46,128,146),'korea':(33,39,124,130),'alaska':(52,72,-170,-140),'canadaE':(42,50,-70,-52),'europe':(47,56,3,15),'usE':(36,45,-80,-68)}.items():
  c=[r for r in out if la0<=r['lat']<=la1 and lo0<=r['lon']<=lo1 and r['users']<r['umax']]
  print('==',reg,len(c))
  for r in c[:12]: print(r['url'],r['users'],r['umax'],r['snr'],r['loc'])
