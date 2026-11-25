from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
def edit(name,old,new):
    p=root/name;s=p.read_text(encoding='utf-8');assert s.count(old)==1,(name,old,s.count(old));p.write_text(s.replace(old,new),encoding='utf-8')
edit('src/main.c','static FILE *restart_hold;','''static FILE *restart_hold;
/* Fixed phase names only. No paths, tokens, account data or command contents. */
static void restart_trace(Manager *m,const char *phase) {
    if (!restart_hold) return;
    Path path; Error ignored={0};
    if (path_join(&path,m->data.p,"update-launch-phase.txt"))
        write_atomic(path.p,phase,strlen(phase),&ignored);
}''')
edit('src/main.c','    m->quit=1;return 1;\n#endif','    restart_trace(m,"APPROVED");\n    m->quit=1;return 1;\n#endif')
edit('src/main.c','    for (size_t i=0;i<ARRAY_LEN(workers);++i) if (workers[i].process.handle) {\n        process_stop','    restart_trace(m,"STOPPING_WORKERS");\n    for (size_t i=0;i<ARRAY_LEN(workers);++i) if (workers[i].process.handle) {\n        process_stop')
edit('src/main.c','    quota_dispose(m);\n    remove_file','    restart_trace(m,"STOPPING_QUOTA");\n    quota_dispose(m);\n    restart_trace(m,"CLOSING_UI");\n    remove_file')
edit('src/main.c','done:\n    runner_free(m);\n    if (restart_hold) {\n        release_instance();','done:\n    restart_trace(m,"FREEING_RUNNER");\n    runner_free(m);\n    if (restart_hold) {\n        release_instance();\n        restart_trace(m,"INSTANCE_RELEASED");')
edit('src/main.c','            result=1;\n        }\n        fclose(restart_hold);','            result=1;\n        }\n        restart_trace(m,result?"LAUNCH_FAILED":"LAUNCH_ACCEPTED");\n        fclose(restart_hold);')
edit('src/platform.c','int launch_verified_update(const char *exe,const char *root,int headless,Error *e) {\n    Buf cmd','''static void shell_trace(const char *root,const char *phase) {
    Path path; Error ignored={0};
    if (path_join(&path,root,"update-launch-phase.txt"))
        write_atomic(path.p,phase,strlen(phase),&ignored);
}
int launch_verified_update(const char *exe,const char *root,int headless,Error *e) {
    Buf cmd''')
edit('src/platform.c','    int32_t com=CoInitializeEx(NULL,2|4);\n    ShellLaunch launch=', '    shell_trace(root,"COM_INITIALIZING");\n    int32_t com=CoInitializeEx(NULL,2|4);\n    ShellLaunch launch=')
edit('src/platform.c','    int ok=program && args && com>=0 && ShellExecuteExW(&launch);\n    DW code=ok?0:GetLastError();','    shell_trace(root,"WINDOWS_SHELL_PENDING");\n    int ok=program && args && com>=0 && ShellExecuteExW(&launch);\n    DW code=ok?0:GetLastError();\n    shell_trace(root,ok?"WINDOWS_SHELL_ACCEPTED":"WINDOWS_SHELL_FAILED");')
edit('tests/windows-update-smoke.ps1',"    throw 'Old Manager did not exit within 30 seconds; Windows shell launch may be awaiting a security prompt. No prompt is bypassed.'",'''    $phaseFile=Join-Path $storage 'update-launch-phase.txt'
    $phase=if(Test-Path -LiteralPath $phaseFile){[IO.File]::ReadAllText($phaseFile)}else{'NOT_RECORDED'}
    $child.Refresh()
    Write-Output "Handoff phase: $phase; original PID: $($child.Id); session: $($child.SessionId)"
    Get-Process -Name 'smartscreen','consent','update-native-test' -ErrorAction SilentlyContinue | Select-Object ProcessName,Id,SessionId,MainWindowTitle | Format-Table -AutoSize | Out-String | Write-Output
    throw "Old Manager did not exit within 30 seconds; phase=$phase. No Windows prompt is bypassed."''')
print('PASS: bounded phase diagnostics, approval and original shell protections unchanged')
