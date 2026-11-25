from pathlib import Path
import sys,os,hashlib
os.chdir(Path(sys.argv[1]).resolve())
before={'src/main.c':'79f47e6361385f53e9f0a2cbc63c1952140a5453ec730cfc6ce9423a27a27962','src/platform.c':'2ddd620301ba8801724cbc3e44ac56e4a170a61ab589d6f2fb06e474bfb24e5c','src/base.h':'31a56bf54213e12fa58b5fb15e15340ed5c23b904d38cb96ca7321580ad47e66','tools/imports.txt':'d4d732118ca3ac10cfa90fe2a9fe64d32648266b861e0862fdbb08fb9384ae3b','tests/windows-update-smoke.ps1':'4c7c3647a6b0e83509c0564947b32ebce3ef779614c93b733ae25eccb5752b6f'}
after={'src/main.c':'826966ebe20715e6b9165981867f63838e3879f53faa2e097f078437c6542e17','src/platform.c':'bbc082333feaee92bff6e6af0d7291f23f5fc4117a38487d4242348eaf7c2964','src/base.h':'a0056607e2767e0cbeccfb1547e84a783b91a1791dbefa7f12f029586deff829','tools/imports.txt':'69043424b36515809ae477cab27dec07ee3054c5e814c11d3deebf367bf76568','tests/windows-update-smoke.ps1':'163f09e7d7bc40ff75d4eac237fcbb9406be66cc59c4a5a084762fb668154c30'}
for name,digest in before.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,('unexpected source',name)
def replace(path,old,new):
    p=Path(path);s=p.read_text(encoding='utf-8');assert s.count(old)==1,(path,old[:100],s.count(old));p.write_text(s.replace(old,new),encoding='utf-8')
replace('src/platform.c','extern intptr_t ShellExecuteW(H, const W *, const W *, const W *, const W *, int);','''extern intptr_t ShellExecuteW(H, const W *, const W *, const W *, const W *, int);
typedef struct {
    DW cb,mask; H hwnd; const W *verb,*file,*parameters,*directory; int show;
    H instance, idlist; const W *class_name; H class_key; DW hotkey; H icon,process;
} ShellLaunch;
extern int ShellExecuteExW(ShellLaunch *);''')
replace('src/platform.c','''int launch_verified_update(const char *exe,const char *root,int headless) {
    Buf cmd={0}; quote_arg(&cmd,"--data-dir");buffer_char(&cmd,' ');quote_arg(&cmd,root);if(headless)buffer_text(&cmd," --headless");
    W *program=wide(exe), *args=wide(cmd.s);
    intptr_t result=program && args?ShellExecuteW(NULL,WC("open"),program,args,NULL,1):0;
    free(program);free(args);buffer_free(&cmd);return result>32;
}''','''int launch_verified_update(const char *exe,const char *root,int headless,Error *e) {
    Buf cmd={0}; quote_arg(&cmd,"--data-dir");buffer_char(&cmd,' ');quote_arg(&cmd,root);if(headless)buffer_text(&cmd," --headless");
    W *program=wide(exe), *args=wide(cmd.s);
    /* ShellExecuteEx needs an initialized COM apartment. NOASYNC ensures the
     * shell completes launch before this process exits; keep Windows prompts. */
    int32_t com=CoInitializeEx(NULL,2|4);
    ShellLaunch launch={.cb=sizeof(launch),.mask=0x40|0x100,.verb=WC("open"),.file=program,.parameters=args,.show=1};
    int ok=program && args && com>=0 && ShellExecuteExW(&launch);
    DW code=ok?0:GetLastError();
    if (launch.process) CloseHandle(launch.process);
    if (com>=0) CoUninitialize();
    free(program);free(args);buffer_free(&cmd);
    return ok || errorf(e,"Windows không khởi chạy được bản mới (Win32 %u, COM 0x%08x). EXE cũ và dữ liệu vẫn giữ nguyên.",code,(unsigned)com);
}''')
replace('src/platform.c','int launch_verified_update(const char *exe,const char *root,int headless) { (void)exe;(void)root;(void)headless;return 0; }','int launch_verified_update(const char *exe,const char *root,int headless,Error *e) { (void)exe;(void)root;(void)headless;return errorf(e,"Chỉ hỗ trợ Windows."); }')
replace('src/base.h','int launch_verified_update(const char *exe,const char *root,int headless);','int launch_verified_update(const char *exe,const char *root,int headless,Error *e);')
replace('tools/imports.txt','shell32 ShellExecuteW ','shell32 ShellExecuteW ShellExecuteExW ')
replace('src/main.c','''        if (!launch_verified_update(approved_candidate.path.p,m->data.p,headless)) {
            alert_user("Không mở được bản mới hoặc Windows đã từ chối. EXE cũ và dữ liệu vẫn được giữ nguyên; mở lại bản cũ để tiếp tục.");result=1;
        }''','''        Error launch_error={0};
        if (!launch_verified_update(approved_candidate.path.p,m->data.p,headless,&launch_error)) {
            Path log; Error ignored={0};
            if (path_join(&log,m->data.p,"update-launch-error.txt")) write_atomic(log.p,launch_error.msg,strlen(launch_error.msg),&ignored);
            if (!headless) alert_user(launch_error.msg);
            result=1;
        }''')
replace('tests/windows-update-smoke.ps1',"  if(!$child.WaitForExit(30000) -or $child.ExitCode -ne 0) {throw 'Old Manager failed to exit safely'}",'''  if(!$child.WaitForExit(30000)) {
    throw 'Old Manager did not exit within 30 seconds; Windows shell launch may be awaiting a security prompt. No prompt is bypassed.'
  }
  if($child.ExitCode -ne 0) {
    $detail=Join-Path $storage 'update-launch-error.txt'
    $reason=if(Test-Path -LiteralPath $detail){[IO.File]::ReadAllText($detail)}else{'No launch error recorded'}
    throw "Old Manager exit code $($child.ExitCode): $reason"
  }''')
for name,digest in after.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,('unexpected patched source',name)
print('PASS: COM shell launch with native prompts retained and exact locally tested patch')
