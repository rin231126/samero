from pathlib import Path
import hashlib, lzma, subprocess, sys
root=Path(__file__).resolve().parent.parent
app=Path(sys.argv[1]).resolve()
raw=(root/'scripts/unified-public-r3.patch.xz').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='51b07e8579c36ed19b644a6525d4a57896c475916312f3eafaf0e1ea3f0f9bb7'
patch=lzma.decompress(raw)
assert hashlib.sha256(patch).hexdigest()=='3f4305e5219fb652a79900f2a24bba1d8177ab7acb785b994c5a47df0cbf3f0a'
before={
'src/base.h':'196874d643f018153a99e66ab6b8746ea598229cdd731e0696ac09a3fcb79bea',
'src/main.c':'80598f12d8e2629a74c039992b03834158206cd8d85c221e5c9ce39721bbf469',
'src/manager.h':'c233486b12df1f059e91dbe251391a9437aed8576964200d34bf749f369dab98',
'src/platform.c':'445da485d6192aeae9ceebe54d34c22b36bc8405e8ea1acbc697438934337680',
'src/update.c':'70fc25e197d98427e33572cd658728af447953ac626981e20c88edde95fa1a5c',
'web/app.js':'34ab6f475b05e644925c9bdd3a2f020bf2ec3aaa6fce6121f3e9f0f452ecc98d',
'web/index.html':'05f52c54520414b5414f3ca00098d8e6ec80d76766767e0c2861025430d3a803',
'tests/update-ui.cjs':'849988dad38e0942e13bc70ccc6db052747652a1d23ec3fe77889e60af9d46a4'}
after={
'src/base.h':'31a56bf54213e12fa58b5fb15e15340ed5c23b904d38cb96ca7321580ad47e66',
'src/main.c':'79f47e6361385f53e9f0a2cbc63c1952140a5453ec730cfc6ce9423a27a27962',
'src/manager.h':'b01a5976d1c9eca21fcc9dead73519018bbea334983340134b2030fe9f3b19c3',
'src/platform.c':'2ddd620301ba8801724cbc3e44ac56e4a170a61ab589d6f2fb06e474bfb24e5c',
'src/update.c':'03c3555e43a9bb93d67132cf77e13a71946a4df2cfb099e1e4ad22be324113e6',
'web/app.js':'6c55b91775be3dedf4faf3eee9061d71ae7ee9fd115b70e804d2fbb2094aca40',
'web/index.html':'80e905dc0bc2ccb2ccda8a81abefba4de67a2ea326cf99f584f5220c350a70a4',
'tests/update-ui.cjs':'511318912af4791a3ce040be4d74a2129f2bb7165d3042a5f8dce2e4c95b66ca',
'tests/update-stage.c':'a911693a51727ea487eb58958f8abf2eb11b1d752f6a181af079c6ffa613c7d1',
'tests/update-restart.c':'8ec80cfef25c5663cc007814cc07fcdf0a146e50bdc36ad97600521775263cd8',
'tests/windows-update-smoke.ps1':'4c7c3647a6b0e83509c0564947b32ebce3ef779614c93b733ae25eccb5752b6f'}
for name,digest in before.items(): assert hashlib.sha256((app/name).read_bytes()).hexdigest()==digest,('unexpected baseline',name)
for name in after.keys()-before.keys(): assert not (app/name).exists(),name
subprocess.run(['git','apply','--check','--unsafe-paths','-'],input=patch,cwd=app,check=True)
subprocess.run(['git','apply','--unsafe-paths','-'],input=patch,cwd=app,check=True)
for name,digest in after.items(): assert hashlib.sha256((app/name).read_bytes()).hexdigest()==digest,('unexpected final',name)
assert not (app/'DEVELOPER-SOURCE.txt').exists()
assert not (app/'src/developer-memory.c').exists()
print('PASS: exact Public-only R3 source, patch and all output digests')
