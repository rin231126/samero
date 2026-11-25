"""Publish only the native-Windows-tested public executable and matching metadata."""
from pathlib import Path
import os, json, hashlib
root=Path(__file__).resolve().parent.parent
exe=root/'downloads/SAMERO-1.0.0-rc1.exe'
source=root/'release-work/SAMERO-1.0.0-rc1.exe'
assert exe.read_bytes()==source.read_bytes(), 'published executable mismatch'
seq=int(os.environ['GITHUB_RUN_NUMBER'])
assert 0<seq<2**31
p=exe.parent/'public-update.json'
payload={'schema':1,'channel':'public','version':'1.0.0-rc1','sequence':seq,'sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'bytes':exe.stat().st_size}
assert 0<payload['bytes']<=64*1024*1024
if p.exists():
    old=json.loads(p.read_text())
    assert old['channel']=='public' and old['version']==payload['version']
    assert old['sequence']<seq or old==payload, 'refusing rollback or sequence reuse'
p.write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n')
print('PASS: public update metadata corresponds to verified executable',seq)
