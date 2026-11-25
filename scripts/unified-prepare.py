from pathlib import Path
import hashlib, zipfile, shutil, os
ROOT=Path(__file__).resolve().parent.parent
WORK=ROOT/'release-work'
APP=WORK/'app'
archive=ROOT/'release-input/SAMERO-1.0.0-rc1-input.zip'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='0008986b73110f6d6d76c31f3ad0c766b14779a3ec39d47907be28e988ab74fb'
APP.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for item in z.infolist():
        p=Path(item.filename)
        assert not p.is_absolute() and '..' not in p.parts and not item.is_dir()
        assert (item.external_attr >> 16) & 0o170000 != 0o120000
        dest=APP/p
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(z.read(item))
p=APP/'tests/windows-smoke.ps1'
s=p.read_text()
assert "if ($settings.version -ne '1.8.1-pixel-rc1')" in s
p.write_text(s.replace("if ($settings.version -ne '1.8.1-pixel-rc1')","if ($settings.version -ne '1.0.0-rc1')"))
p=APP/'PROJECT_STATUS.md'
p.write_text('# SAMERO — 1.0.0-rc1 (first public release candidate)\n\n- First public version follows internal 1.9.0-studio-rc1.\n- Six updated role sprites are shared by app and website; original logo retained. No change to runner or persistent data format.\n- See TEST-RESULTS.txt for verified and unverified checks.\n- Older sections below are historical records.\n\n'+p.read_text())
p=APP/'tools/studio_assets.py'
s=p.read_text()
assert ' im.save(out/p.name,optimize=True)' in s
p.write_text(s.replace(' im.save(out/p.name,optimize=True)',' (out/p.name).write_bytes(p.read_bytes())'))
assert '#define SAM_VERSION "1.0.0-rc1"' in (APP/'src/manager.h').read_text()
for f in (APP/'tools/launch-role-art').glob('*.png'):
    assert f.read_bytes()==(APP/'web/mascot'/f.name).read_bytes()
print('PASS: original source archive digest, safe extraction, 1.0.0 version, canonical role bytes')


# Ubuntu's GCC can inject glibc-only fortified libc symbols by default.
# The custom Windows PE cross-link path uses Win32/MSVCRT, not glibc.
# Keep Linux compiler defaults and all existing PE link mitigations unchanged.
p=APP/'tools/build.py'
s=p.read_text()
old='run("gcc", *flags, "-DSAM_WINDOWS", "-mabi=ms",'
new='run("gcc", *flags, "-U_FORTIFY_SOURCE", "-D_FORTIFY_SOURCE=0", "-DSAM_WINDOWS", "-mabi=ms",'
assert s.count(old)==1, 'unexpected Windows compiler invocation'
p.write_text(s.replace(old,new))
