import json, subprocess, sys, tempfile, time, urllib.request, urllib.error
from pathlib import Path
exe=Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as td:
 p=subprocess.Popen([str(exe),'--data-dir',td],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  path=Path(td)/'ui.url'; deadline=time.monotonic()+10
  while not path.exists():
   assert p.poll() is None and time.monotonic()<deadline;time.sleep(.05)
  origin,key=path.read_text().split('/#')
  def api(action,body,key=key):
   req=urllib.request.Request(origin+'/api/'+action,data=json.dumps(body).encode(),headers={'Origin':origin,'Content-Type':'application/json','X-Samero-Key':key})
   with urllib.request.urlopen(req,timeout=4) as res: return json.load(res)
  a='a'*32;b='b'*32
  try:api('ui-lease',{'id':a},'c'*32);raise AssertionError('unauthorized heartbeat accepted')
  except urllib.error.HTTPError as e:assert e.code==403
  api('ui-lease',{'id':a});api('ui-lease',{'id':b});api('ui-lease',{'id':a,'closing':True})
  time.sleep(16);assert p.poll() is None;api('state',{})
  print('PASS: unauthorized lease denied; second window keeps Manager alive',flush=True)
  api('ui-lease',{'id':b,'closing':True});assert p.wait(timeout=23)==0
  assert not path.exists() and not (Path(td)/'ui.version').exists()
  print('PASS: closing last idle UI exits server and removes runtime URL files',flush=True)
 finally:
  if p.poll() is None:p.terminate();p.wait(timeout=5)
with tempfile.TemporaryDirectory() as td:
 p=subprocess.Popen([str(exe),'--headless','--data-dir',td],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  path=Path(td)/'ui.url';deadline=time.monotonic()+10
  while not path.exists():
   assert p.poll() is None and time.monotonic()<deadline;time.sleep(.05)
  origin,key=path.read_text().split('/#')
  req=urllib.request.Request(origin+'/api/exit',data=b'{}',headers={'Origin':origin,'Content-Type':'application/json','X-Samero-Key':key})
  with urllib.request.urlopen(req,timeout=4) as res:assert res.status==200
  assert p.wait(timeout=5)==0
  print('PASS: explicit authenticated headless shutdown remains available',flush=True)
 finally:
  if p.poll() is None:p.terminate();p.wait(timeout=5)
