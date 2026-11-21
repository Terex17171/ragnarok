import json, random, time, threading, secrets, urllib.request, re
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs,urlparse
ROOT=Path(__file__).parent
lock=threading.RLock(); rooms={}; monsters={}
# Official rAthena community database: renewal and pre-renewal union.
def load():
 for mode in ('re','pre-re'):
  url=f'https://raw.githubusercontent.com/rathena/rathena/master/db/{mode}/mob_db.yml'
  data=urllib.request.urlopen(url,timeout=40).read().decode()
  for block in re.split(r'(?m)^  - Id: ',data)[1:]:
   mid=int(block.splitlines()[0]); m=re.search(r'(?m)^    Name: (.+)$',block)
   if m: monsters.setdefault(mid,m.group(1).strip().strip('"\''))
 if len(set(monsters.values()))<4: raise RuntimeError('Monster database unavailable')
def advance(r):
 if r['phase']=='question' and time.time()>=r['until']: r.update(phase='reveal',until=time.time()+4,winner=None)
 if r['phase']=='reveal' and time.time()>=r['until']:
  if r['round']>=r['total']: r['phase']='finished';return
  mid=random.choice([i for i in monsters if i not in r['used']] or list(monsters));r['used'].append(mid); name=monsters[mid]; opts=random.sample(sorted(set(monsters.values())-{name}),3)+[name];random.shuffle(opts)
  r.update(phase='question',round=r['round']+1,mid=mid,options=opts,correct=opts.index(name),until=time.time()+15,wrong=[],winner=None)
class H(SimpleHTTPRequestHandler):
 def __init__(self,*a,**k):super().__init__(*a,directory=str(ROOT),**k)
 def reply(self,d,status=200):
  b=json.dumps(d).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
 def do_GET(self):
  u=urlparse(self.path)
  if u.path!='/state':return super().do_GET()
  q=parse_qs(u.query)
  with lock:
   r=rooms.get(q.get('room',[''])[0]); token=q.get('token',[''])[0]
   if not r or token not in r['players']:return self.reply({'error':'Room or player not found'},404)
   advance(r); d={k:v for k,v in r.items() if k not in ('players','correct','host','used','wrong')};d.update(players=sorted(r['players'].values(),key=lambda p:-p['score']),host=token==r['host'],locked=token in r.get('wrong',[]),now=time.time(),count=len(monsters));
   if r['phase'] in ('reveal','finished'):d['correct']=r.get('correct')
   self.reply(d)
 def do_POST(self):
  try:
   d=json.loads(self.rfile.read(int(self.headers['Content-Length']))); action=self.path;token=d.get('token');code=d.get('room','').upper()
   with lock:
    if action=='/join':
     if not code:
      code=secrets.token_hex(3).upper(); rooms[code]={'players':{},'host':None,'phase':'lobby','round':0,'total':20,'used':[],'until':0}
     r=rooms.get(code)
     if not r or r['phase']!='lobby':return self.reply({'error':'Room not available'},400)
     token=secrets.token_urlsafe(18);r['players'][token]={'name':str(d.get('name','Player')).strip()[:24] or 'Player','score':0};r['host']=r['host'] or token;return self.reply({'room':code,'token':token})
    r=rooms.get(code)
    if not r or token not in r['players']:return self.reply({'error':'Invalid player'},403)
    advance(r)
    if action=='/start' and token==r['host'] and r['phase'] in ('lobby','finished'):
     r.update(total=max(1,min(50,int(d.get('total',20)))),round=0,used=[],phase='reveal',until=0);[p.update(score=0) for p in r['players'].values()];advance(r)
    elif action=='/answer' and r['phase']=='question' and d.get('round')==r['round'] and token not in r['wrong']:
     if d.get('choice')==r['correct']:
      r['players'][token]['score']+=1;r.update(phase='reveal',winner=r['players'][token]['name'],until=time.time()+4)
     else:r['wrong'].append(token)
    self.reply({'ok':True})
  except Exception:self.reply({'error':'Invalid request'},400)
if __name__=='__main__':
 import os
 print('Loading monster databases...',flush=True);load();print(f'{len(monsters)} monsters loaded. Open http://localhost:8000',flush=True);ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT',8000))),H).serve_forever()
