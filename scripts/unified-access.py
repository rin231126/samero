from pathlib import Path
import os, sys, hashlib
os.chdir(Path(sys.argv[1]).resolve())
before={'src/chat.c':'994d435deffca55515d5097c22652ef7940a8b3454eec33783b1dcd82427875e','src/runner.c':'ad53958402fe15f4fb0bac7524015fb492c273bb0da24749ae5505dd52153a88','web/app.js':'17cd14e15139a4a3eab425eece70f7c55e8370b7245e2f71e3fe6b366473e833','tests/integration.py':'f542ee5d8c3f6d2ce299d1be311e6d3effe3aba90a45a7c25ed9be1c12037b67'}
after={'src/chat.c':'90588b4394b1b6316461b73c7dc1d05d7c136b451fcec2c727d108c5cf41dd3d','src/runner.c':'ad6acf31846d597e3f6615ce34b709a25e0751cdfe3227cb82cd8693931ecd9d','web/app.js':'cdd57a3aa1a8d70997df95ce4cfefcb2a25e33fd416a17d928d969d67ba16ea0','tests/integration.py':'54d09d83d8117de9018bcba9268f910bbb99526bfb6944b846e5e4ebdfd7046a'}
for name,digest in before.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,('unexpected baseline',name)
p=Path('src/chat.c');s=p.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,(a[:100],s.count(a));s=s.replace(a,b)
replace('Buf incoming, draft, diff, tool_output, runner_result;', 'Buf incoming, draft, diff, tool_output, runner_result, access_policy;\n    int access_request, access_checked;')
replace('static void thread_ready(Manager *m,Live *l) {',r'''/* Probe only fixed bookkeeping files through the server's own confirmed read-only
 * sandbox. No contents, host-side fallback, or permission escalation. */
static void access_hold(Manager *m,Live *l,const char *reason) {
    l->chat->access_request=0;
    connection_failed(m,l,"startup",reason);
    runner_review_denied(m,l,reason);
}
static int access_probe(Manager *m,Live *l) {
    Chat *c=l->chat;
    if (!c->access_policy.n) { access_hold(m,l,"BLOCKED_PREFLIGHT: Codex chưa xác nhận chính sách chỉ đọc."); return 0; }
    Buf params={0};
    buffer_text(&params,"{\"command\":[");
    json_quote(&params,terminal_program());
#ifdef SAM_WINDOWS
    buffer_text(&params,",\"-NoLogo\",\"-NoProfile\",\"-NonInteractive\",\"-Command\",");
    json_quote(&params,"$ErrorActionPreference='Stop'; foreach($name in @('TASK_QUEUE.json','PROJECT_STATUS.md')) { try { $s=[IO.File]::OpenRead([IO.Path]::Combine((Get-Location).Path,$name)); try {$null=$s.ReadByte()} finally {$s.Dispose()} } catch { [Console]::Error.WriteLine('SAMERO_READ_FAILED '+$name+' '+$_.Exception.GetBaseException().GetType().Name); exit 13 } }; [Console]::WriteLine('SAMERO_READ_OK')");
#else
    buffer_text(&params,",\"--noprofile\",\"--norc\",\"-c\",");
    json_quote(&params,"for name in TASK_QUEUE.json PROJECT_STATUS.md; do if ! head -c 1 -- \"$name\" >/dev/null; then printf 'SAMERO_READ_FAILED %s\\n' \"$name\" >&2; exit 13; fi; done; printf 'SAMERO_READ_OK\\n'");
#endif
    buffer_char(&params,']'); KEY(&params,"cwd",l->workspace.p);
    RAW(&params,"sandboxPolicy",c->access_policy.s);
    NUM(&params,"timeoutMs",10000); NUM(&params,"outputBytesCap",2048);
    buffer_char(&params,'}');
    c->access_request=c->next++;
    c->deadline=monotonic_ms()+15000;
    stage(c,"starting");
    int ok=codex_send(&l->process,c->access_request,"command/exec",params.s);
    buffer_free(&params);
    if (!ok) access_hold(m,l,"BLOCKED_PREFLIGHT: Không gửi được command/exec kiểm tra quyền đọc.");
    return ok;
}
static void thread_ready(Manager *m,Live *l) {''')
replace('    c->deadline=0; c->load_retry=0; c->loaded=1;\n    c->thread_committed=', '''    c->deadline=0; c->load_retry=0; c->loaded=1;
    if (l->read_only_turn && !c->access_checked && !strncmp(c->first,"SAMERO VERIFY.",14)) {
        access_probe(m,l); return;
    }
    c->thread_committed=''')
replace('    if (id==c->loaded_request && c->loaded_request) {',r'''    if (id==c->access_request && c->access_request) {
        c->access_request=0; c->deadline=0;
        long long code=json_int(j,json_get(j,result,"exitCode"),-1);
        long long rpc_code=json_int(j,json_get(j,err,"code"),0);
        char output[2049],detail[2049],message[520];
        json_field(j,result,"stdout",output,sizeof(output));
        json_field(j,result,"stderr",detail,sizeof(detail));
        if (err>=0 && rpc_code==-32601) {
            /* Legacy server: no preflight assertion; normal verifier still required. */
            log_system(m,l,"CLI không hỗ trợ command/exec; kiểm tra trước chưa xác minh. VERIFY vẫn phải đọc bằng chứng gốc.");
            c->access_checked=1; thread_ready(m,l); return;
        }
        runner_record_command(m,l,"command/exec: read-only preflight of TASK_QUEUE.json and PROJECT_STATUS.md (no file contents)",code);
        if (result>=0 && code==0 && (!strcmp(output,"SAMERO_READ_OK\n") || !strcmp(output,"SAMERO_READ_OK\r\n"))) {
            log_system(m,l,"Kiểm tra trước: App Server đã đọc được hai tệp quản lý trong sandbox chỉ đọc. Không thay thế nghiệm thu Task.");
            c->access_checked=1; thread_ready(m,l); return;
        }
        const char *file=strstr(detail,"SAMERO_READ_FAILED TASK_QUEUE.json")?"TASK_QUEUE.json":
            strstr(detail,"SAMERO_READ_FAILED PROJECT_STATUS.md")?"PROJECT_STATUS.md":"TASK_QUEUE.json / PROJECT_STATUS.md";
        const char *kind=contains_ci(detail,"UnauthorizedAccessException") || contains_ci(detail,"Permission denied") || contains_ci(detail,"Access is denied")?"BLOCKED_ACCESS":"BLOCKED_PREFLIGHT";
        const char *cause=contains_ci(detail,"FileNotFoundException") || contains_ci(detail,"No such file")?"Không tìm thấy tệp.":
            !strcmp(kind,"BLOCKED_ACCESS")?"Quyền đọc bị từ chối.":"Chưa xác định được nguyên nhân; kiểm tra quyền, workspace và CLI.";
        sam_format(message,sizeof(message),"%s: command/exec chỉ đọc: %s; exit %lld, RPC %lld. %s Không gửi VERIFY.",kind,file,code,rpc_code,cause);
        access_hold(m,l,message); return;
    }
    if (id==c->loaded_request && c->loaded_request) {''')
replace('        c->idle_in_reply=!strcmp(status,"idle");', '''        if (l->read_only_turn) { buffer_free(&c->access_policy); json_raw(&c->access_policy,j,box); }
        c->idle_in_reply=!strcmp(status,"idle");''')
replace('    if (c->deadline && monotonic_ms()>c->deadline) {\n        if (!strcmp(c->stage,"starting"))', '''    if (c->deadline && monotonic_ms()>c->deadline) {
        if (c->access_request) { access_hold(m,l,"BLOCKED_PREFLIGHT: command/exec kiểm tra quyền đọc vượt thời gian chờ. Không gửi VERIFY."); return; }
        if (!strcmp(c->stage,"starting"))''')
replace('    buffer_free(&c->runner_result); buffer_free(&c->incoming);','    buffer_free(&c->access_policy); buffer_free(&c->runner_result); buffer_free(&c->incoming);')
# Explicitly prevent unexpected permission requests from read-only verification.
replace('    Approval *a=NULL;\n    for (size_t i=0;i<ARRAY_LEN(c->approvals);++i)', '''    if (l->read_only_turn) {
        reply(l,rpc_id,"decline");
        const char *why="BLOCKED_ACCESS: Codex yêu cầu phê duyệt thao tác ngoài quyền của phiên chỉ đọc. Kiểm tra cấu hình hợp lệ.";
        log_system(m,l,why); runner_review_denied(m,l,why); return;
    }
    Approval *a=NULL;
    for (size_t i=0;i<ARRAY_LEN(c->approvals);++i)''')
p.write_text(s)
p=Path('src/runner.c');s=p.read_text()
replace('    if (!strncmp(s,"BLOCKED_RESOURCE:",17)) return "BLOCKED_RESOURCE";', '    if (!strncmp(s,"BLOCKED_RESOURCE:",17)) return "BLOCKED_RESOURCE";\n    if (!strncmp(s,"BLOCKED_PREFLIGHT:",18)) return "BLOCKED_PREFLIGHT";')
replace('            hold(m,r,REVIEW,reason);\n            return;', '''            if (r->phase==VERIFY && r->index<r->count && *review_blocker(reason) && !secret_text(reason))
                sam_format(r->tasks[r->index].evidence,sizeof(r->tasks[r->index].evidence),"%s",reason);
            hold(m,r,REVIEW,reason);
            return;''')
p.write_text(s)
p=Path('web/app.js');s=p.read_text()
replace('"Codex báo thiếu tài nguyên bắt buộc. Bổ sung tài nguyên trước RESUME."','r.blocker==="BLOCKED_PREFLIGHT"?"Kiểm tra trước không thành công. Xem Chẩn đoán để kiểm tra CLI và workspace trước RESUME.":"Codex báo thiếu tài nguyên bắt buộc. Bổ sung tài nguyên trước RESUME."')
p.write_text(s)
p=Path('tests/integration.py');s=p.read_text()
replace('    elif method == "turn/start":\n        if (home/"reject-turn")', '''    elif method == "command/exec":
        assert sandbox=="read-only" and p["cwd"]==os.getcwd()
        assert p["sandboxPolicy"]=={"type":"readOnly","networkAccess":False}
        assert p["timeoutMs"]==10000 and p["outputBytesCap"]==2048
        if (home/"preflight-unsupported").exists():
            emit({"id":r["id"],"error":{"code":-32601,"message":"Method not found"}})
        elif (home/"preflight-denied").exists():
            result(r,{"exitCode":13,"stdout":"","stderr":"SAMERO_READ_FAILED TASK_QUEUE.json UnauthorizedAccessException"})
        else:
            result(r,{"exitCode":0,"stdout":"SAMERO_READ_OK\\n","stderr":""})
    elif method == "turn/start":
        if (home/"reject-turn")''')
replace('    def test_resume_access_blocker_reuses_matching_test(self):', '''    def test_preflight_denied_stops_before_verify_and_resume_recovers(self):
        cmd=self.runner_fixture();home=self.root/"Autonomous"; (home/"preflight-denied").touch()
        rid=self.req("runner-start",cmd)["id"];ctl={"project":cmd["project"],"id":rid,"confirmed":True}
        r=self.run_state(rid,lambda r:r["mode"]=="review" and not r["snapshot"])
        self.assertEqual((r["index"],r["phase"],r["blocker"]),(0,"verify","BLOCKED_ACCESS"))
        self.assertIn("TASK_QUEUE.json",r["reason"])
        sid=r["tasks"][0]["testSession"]
        self.assertTrue(sid)
        msgs=[json.loads(x) for x in (home/"rpc.jsonl").read_text().splitlines()]
        self.assertFalse(any(x.get("method")=="turn/start" and x["params"]["input"][0]["text"].startswith("SAMERO VERIFY.") for x in msgs))
        (home/"preflight-denied").unlink()
        self.req("runner-resume",ctl)
        r=self.run_state(rid,lambda r:r["mode"] in ("done","review","blocked") and not r["snapshot"])
        self.assertEqual((r["mode"],r["index"]),("done",2),r["reason"])
        self.assertEqual(r["tasks"][0]["testSession"],sid)

    def test_preflight_unsupported_does_not_fake_verification(self):
        cmd=self.runner_fixture();home=self.root/"Autonomous"; (home/"preflight-unsupported").touch(); (home/"blocked-access").touch()
        rid=self.req("runner-start",cmd)["id"]
        r=self.run_state(rid,lambda r:r["mode"]=="review" and not r["snapshot"])
        self.assertEqual((r["index"],r["phase"],r["blocker"]),(0,"verify","BLOCKED_ACCESS"))
        self.assertFalse(r["tasks"][0]["verifySession"])

    def test_resume_access_blocker_reuses_matching_test(self):''')
p.write_text(s)
for name,digest in after.items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,('unexpected patched file',name)
print('PASS: exact locally tested access preflight and regression source')
