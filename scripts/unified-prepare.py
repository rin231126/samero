from pathlib import Path
import hashlib, zipfile, shutil, os, sys
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
p.write_text('# SAMERO — 1.0.0-rc1 (first public release candidate)\n\n- First public version follows internal 1.9.0-studio-rc1.\n- Six updated role sprites are shared by app and website; original logo retained. Runner distinguishes reported blockers and stores optional test fingerprints; older journals remain readable.\n- See TEST-RESULTS.txt for verified and unverified checks.\n- Older sections below are historical records.\n\n'+p.read_text())
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

# Apply the locally tested, reviewable patch to the canonical archive.
import subprocess
expected_before = {
    'src/runner.c': '178e1717360ee4c0d17c994e14e332632b72ea7a51c91631b5361abdfd6fdcba',
    'web/app.js': 'ea85dc1cc44f57a081d63a9ea185abb5a5b2cb9b32971da05f80336392c15f3f',
    'tests/integration.py': '8a029444d7de5e592f7d5b261947dfd1d5977815c3d08d9fd17a17ee72ad0e12',
}
expected_after = {
    'src/runner.c': 'a4c48ca0cc97f9eb82397ce953a9e3422ff09506fc9191696fa3abc6588e2dda',
    'web/app.js': 'de245ce833742c8500e7e23ffe77b25b7358e98580025de6797a14162f30b726',
    'tests/integration.py': 'f542ee5d8c3f6d2ce299d1be311e6d3effe3aba90a45a7c25ed9be1c12037b67',
}
for name, digest in expected_before.items():
    assert hashlib.sha256((APP/name).read_bytes()).hexdigest()==digest, ('unexpected original',name)
patch = ROOT/'scripts/unified-resume.patch'
args = ['git','apply','--directory=release-work/app']
subprocess.run(args+['--check',str(patch)],cwd=ROOT,check=True)
subprocess.run(args+[str(patch)],cwd=ROOT,check=True)
for name, digest in expected_after.items():
    assert hashlib.sha256((APP/name).read_bytes()).hexdigest()==digest, ('unexpected patched source',name)
print('PASS: exact locally tested resume/handover source and regression tests, version unchanged')

# Preserve version 1.0 and add authenticated desktop UI lifetime management.
subprocess.run([sys.executable, str(ROOT/'scripts/unified-lifetime.py'), str(APP)], check=True)

# Probe the confirmed read-only sandbox before spending model quota on VERIFY.
subprocess.run([sys.executable, str(ROOT/'scripts/unified-access.py'), str(APP)], check=True)

# Diagnose OS access without PowerShell and identify same-version source builds.
subprocess.run([sys.executable, str(ROOT/'scripts/unified-diagnostics.py'), str(APP)], check=True)

# Public release notification; independent of private development features.
subprocess.run([sys.executable, str(ROOT/'scripts/unified-public-update.py'), str(APP)], check=True)

# Public R3 streaming download and explicit side-by-side restart.
subprocess.run([sys.executable, str(ROOT/'scripts/unified-public-r3.py'), str(APP)], check=True)

# Preserve Windows launch prompts; initialize COM and report native launch errors.
subprocess.run([sys.executable, str(ROOT/'scripts/unified-update-launch.py'), str(APP)], check=True)

# Pass observed sandbox-read proof to VERIFY and distinguish reported from observed denials.
subprocess.run([sys.executable, str(ROOT/'scripts/unified-verify-evidence.py'), str(APP)], check=True)

# Apply the shared VERIFY diagnostics changes to the prepared Public app.
import lzma
verify_patch = lzma.decompress((ROOT / 'scripts' / 'unified-verify-diagnostics.patch.xz').read_bytes())
verify_apply = ['git', 'apply', '--whitespace=error', '--directory=release-work/app']
subprocess.run([*verify_apply, '--check', '-'], cwd=ROOT, input=verify_patch, check=True)
subprocess.run([*verify_apply, '-'], cwd=ROOT, input=verify_patch, check=True)
print('PASS: Public VERIFY diagnostics applied to the prepared source')

# Use Codex's default command output cap on Windows where the sandbox requires it.
preflight_patch = (ROOT / 'scripts' / 'unified-windows-preflight.patch').read_bytes()
subprocess.run([*verify_apply, '--check', '-'], cwd=ROOT, input=preflight_patch, check=True)
subprocess.run([*verify_apply, '-'], cwd=ROOT, input=preflight_patch, check=True)
print('PASS: Windows sandbox preflight uses the default command output cap')


# R183: port verified runner/UI changes onto the existing PUBLIC source only.
# Preserve the existing public updater and all previously applied public fixes.
def r183_replace(path, old, new):
    p = APP / path
    s = p.read_text(encoding='utf-8')
    assert s.count(old) == 1, ('R183 source context mismatch', path, old[:120])
    p.write_text(s.replace(old, new), encoding='utf-8')

r183_replace('src/runner.c',
    'static void queue_json(const Run *r,Buf *b) {',
    '''static const char *current_verify_blocker(const Run *r) {
    return r->mode==REVIEW && r->phase==VERIFY && r->index<r->count ? review_blocker(r->reason) : "";
}
static void queue_json(const Run *r,Buf *b) {''')
r183_replace('src/runner.c',
    'KEY(b,"blocker",r->mode==REVIEW && r->phase==VERIFY && r->index<r->count?review_blocker(r->tasks[r->index].evidence):"");',
    'KEY(b,"blocker",current_verify_blocker(r));')
r183_replace('src/runner.c',
    'KEY(out,"codexBlocker",r->index<r->count?review_blocker(r->tasks[r->index].evidence):"");',
    'KEY(out,"codexBlocker",current_verify_blocker(r));')
r183_replace('src/runner.c',
    'step(r,VERIFY,r->tasks[r->index].evidence[0]?r->tasks[r->index].evidence:"Đã lưu kết quả test cho nhiệm vụ.");',
    'step(r,VERIFY,"Đã ghi nhận test exit 0. Đang lưu checkpoint trước khi kiểm tra quyền đọc và nghiệm thu.");')
r183_replace('src/runner.c',
    'r->resume_verify=r->phase==VERIFY && *review_blocker(t->evidence) && valid_id(t->test_session);',
    'r->resume_verify=r->phase==VERIFY && valid_id(t->test_session);')
r183_replace('web/app.js',
    'html(t.status)+"<small>"+html(t.evidence)+"</small>"',
    'html(t.status)+"<small>"+html(i===r.index && !r.blocker && t.evidence?.startsWith("BLOCKED_PREFLIGHT:") ? "Lần trước · "+t.evidence : t.evidence)+"</small>"')
r183_replace('web/app.js',
    'Trạng thái Codex gần nhất: ${html(v.codexBlocker||"Chưa xác định")}',
    'Lỗi chặn hiện tại · ${html(v.codexBlocker||"Chưa có")}')

# Do not distribute private Developer capabilities, sources, or data.
assert not (APP/'DEVELOPER-SOURCE.txt').exists()
assert not list((APP/'src').glob('developer-*.c'))
assert not list((APP/'src').glob('developer-*.h'))
assert not (APP/'tools/developer-candidate.py').exists()
for p in [APP/'src/manager.c', APP/'src/main.c', APP/'web/app.js', APP/'web/index.html']:
    s = p.read_text(encoding='utf-8')
    assert not any(x in s for x in ('developer-prepare','developer-start','developerMemory','Tự cải tiến')), ('private Developer feature',str(p))
assert (APP/'src/update.c').is_file(), 'public updater must remain available'
assert '#define SAM_VERSION "1.0.0-rc1"' in (APP/'src/manager.h').read_text()

# Native-independent regression: a stale denial is historical, not a current
# blocker. Successful TEST must not grant VERIFY or discard four accepted tasks.
test = APP/'tests/r183-state.c'
test.write_text(r'''#include "../src/runner.c"
int main(void) {
    Run *run=allocate(sizeof(*run));
    run->count=16; run->index=4; run->phase=TEST; run->mode=ACTIVE;
    strcpy(run->session,"11111111111111111111111111111111");
    for (int i=0;i<4;++i) strcpy(run->tasks[i].evidence,"accepted evidence");
    Task *task=&run->tasks[4];
    const char *old="BLOCKED_PREFLIGHT: command/exec timed out";
    strcpy(task->evidence,old);
    strcpy(task->test_signature,"3333333333333333333333333333333333333333333333333333333333333333");
    strcpy(task->verify_observation,"session=22222222222222222222222222222222");
    Task *expected=allocate(4*sizeof(Task));
    memcpy(expected,run->tasks,4*sizeof(Task));
    check_finished(run,0,"");
    int ok=run->phase==VERIFY && run->mode==ACTIVE && run->index==4 && run->test==1 &&
        run->snapshot && !run->inflight && !strcmp(task->test_session,run->session) &&
        !memcmp(expected,run->tasks,4*sizeof(Task)) && !strcmp(task->evidence,old) &&
        !strcmp(task->test_signature,"3333333333333333333333333333333333333333333333333333333333333333") &&
        !*review_blocker(run->reason);
    run->mode=REVIEW;
    ok=ok && !*current_verify_blocker(run);
    note(run,old);
    ok=ok && !strcmp(current_verify_blocker(run),"BLOCKED_PREFLIGHT");
    free(expected);free(run);
    if (!ok) return 1;
    puts("PASS: R183 historical evidence, current blocker, preserved receipts and TEST-to-VERIFY");
    return 0;
}
''',encoding='utf-8')
import tempfile
with tempfile.TemporaryDirectory(prefix='samero-r183-') as temp:
    executable = Path(temp)/'state-test'
    subprocess.run(['gcc','-std=c11','-D_GNU_SOURCE','-O2','-Wall','-Wextra','-Werror',
        '-ffunction-sections','-fdata-sections',str(test),str(APP/'src/base.c'),
        str(APP/'src/platform.c'),'-Wl,--gc-sections','-o',str(executable)],check=True)
    subprocess.run([str(executable)],check=True)
print('PASS: Public-only R183 runner/UI fix; real authenticated Windows sandbox remains NOT VERIFIED')
