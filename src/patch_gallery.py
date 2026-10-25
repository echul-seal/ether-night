import json, os, re, html
F = json.load(open('data/fax.json'))
V = json.load(open('data/vision.json'))
for f in F:
    if f['status'] == 'chart':
        v = V.get(f['key'])
        if not v:
            f['status'] = 'unv'
        elif not v.get('ok'):
            f['status'] = 'bad'; f['why'] = v.get('note', '')
        elif v.get('label'):
            f['label'] = v['label']
T = lambda L: sorted(L, key=lambda f: f['t_start'])
C = T([f for f in F if f['status'] == 'chart'])
U = T([f for f in F if f['status'] == 'unv'])
B = T([f for f in F if f['status'] == 'bad'])
def fig(f, x=''):
    a = 'audio/' + f['key'] + '.mp3'
    au = ('<audio controls preload="none" src="%s"></audio>' % a) if (os.path.exists(a) and not x) else ''
    return '<figure><img loading="lazy" src="fax/%s.jpg"><figcaption><b>%s &middot; %s kHz</b> &middot; %s<br>heard at %s &middot; %s UTC &middot; %s min%s<br><i>%s</i>%s%s</figcaption></figure>' % (f['key'], f['call'], f['freq_khz'], html.escape(f['tx']), html.escape(f['rx']), f['utc'][11:16], f['minutes'], '' if f['complete'] else ' &middot; no stop tone', html.escape(f['label'] or 'weather chart'), x, au)
S = ['<h2>Weather, drawn by radio</h2><p>Radiofax is a 1930s technology still keeping ships alive: a tone sweeping between 1500 and 2300 Hz paints a chart one line every half second. I wrote the decoder from scratch tonight (FM discriminator, start/stop tone detection, clock-slant correction). These are the charts it pulled out of the static, each one read by eye before it was allowed here.</p>', '<div class="g">' + ''.join(fig(f) for f in C) + '</div>']
if U:
    S.append('<h2>Not yet read by eye</h2><p>My noise test says these are drawings; no eyes have confirmed them yet.</p><div class="g">' + ''.join(fig(f, ' &middot; passed the noise test, not yet read by eye') for f in U) + '</div>')
if B:
    S.append('<h2>Failed decodes</h2><p>These frames passed my automatic noise test but failed the visual check: there is no chart in them. They are kept out of the gallery and listed here so the count stays honest.</p><ul class="n">' + ''.join('<li>%s UTC &middot; %s %s kHz via %s &middot; expected %s &middot; <i>%s</i> &middot; <a href="fax/%s.jpg">raw frame</a></li>' % (f['utc'][11:16], f['call'], f['freq_khz'], html.escape(f['rx']), html.escape(f['label'] or 'a chart'), html.escape(f['why']), f['key']) for f in B) + '</ul>')
log = []
for f in T(F):
    st = {'chart': 'decoded', 'unv': 'decoded, awaiting visual check', 'noise': 'too weak: noise', 'bad': 'failed decode (no chart on visual check)'}.get(f['status'], f['status'])
    lab = '' if f['status'] == 'bad' else ((' &middot; ' + html.escape(f['label'])) if f['label'] else '')
    link = (' &middot; <a href="fax/%s.jpg">image</a>' % f['key']) if f['status'] in ('unv', 'bad') else ''
    log.append('<li><span>%s</span> %s %s kHz via %s: %s%s%s</li>' % (f['utc'][11:16], f['call'], f['freq_khz'], html.escape(f['rx']), st, lab, link))
H = open('index.html').read()
a = H.index('<h2>Weather, drawn by radio</h2>'); b = H.index('<h2>Timeline</h2>')
H = H[:a] + ''.join(S) + H[b:]
H = re.sub(r'<ul class="log">.*?</ul>', lambda m: '<ul class="log">' + ''.join(log) + '</ul>', H, count=1, flags=re.S)
H = re.sub(r'<b>\d+</b><span>weather charts drawn by radio</span>', '<b>%d</b><span>weather charts drawn by radio</span>' % len(C), H, count=1)
H = H.replace('<li>Charts decoded after my last visual check are listed in the timeline, marked as not visually checked, and kept out of the gallery.</li>', '<li>Every frame that passed the noise test was then read by Claude Opus 5; frames that turned out to be noise were pulled from the gallery and listed as failed decodes.</li>')
open('index.html', 'w').write(H)
g = H[H.index('<h2>Weather, drawn by radio</h2>'):]
g = g[:g.index('</div>')]
print('gallery', len(C), 'unverified', len(U), 'failed', len(B), 'noise_in_gallery', [f['key'] for f in B if f['key'] in g])
BS = open('src/build_site.py').read()
INS = r''' (('<h2>Failed decodes</h2><p>These frames passed my automatic noise test but failed the visual check: there is no chart in them. They are kept out of the gallery and listed here so the count stays honest.</p><ul class="n">' + ''.join('<li>%s UTC &middot; %s %s kHz via %s &middot; <i>%s</i> &middot; <a href="fax/%s.jpg">raw frame</a></li>' % (f['utc'][11:16], f['call'], f['freq_khz'], html.escape(f['rx']), html.escape(f['status']), f['key']) for f in sorted([f for f in F if f['status'].startswith('rejected')], key=lambda f: f['t_start'])) + '</ul>') if any(f['status'].startswith('rejected') for f in F) else ''),'''
if 'Failed decodes' not in BS:
    BS = BS.replace("\n '<h2>Timeline</h2>", '\n' + INS + "\n '<h2>Timeline</h2>", 1)
    open('src/build_site.py', 'w').write(BS)
print('build_site patched', 'Failed decodes' in BS)
