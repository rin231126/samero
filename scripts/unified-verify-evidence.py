from pathlib import Path
import sys
root=Path(sys.argv[1]).resolve()
def edit(name,old,new):
    p=root/name;s=p.read_text(encoding='utf-8');assert s.count(old)==1,(name,old[:100],s.count(old));p.write_text(s.replace(old,new),encoding='utf-8')
edit('src/chat.c','int access_request, access_checked;','int access_request, access_checked, access_verified, observed_access_denial;')
edit('src/chat.c','    c->unauthorized=0;\n    c->tool_id[0]=0;','    c->unauthorized=0;\n    c->observed_access_denial=0;\n    c->tool_id[0]=0;')
edit('src/chat.c','            c->access_checked=1; thread_ready(m,l); return;\n        }\n        const char *file=', '            c->access_verified=1; c->access_checked=1; thread_ready(m,l); return;\n        }\n        const char *file=')
edit('src/chat.c','        if (!post_turn(m,l,c->first,&e)) log_system(m,l,e.msg);','''        if (l->autonomous && l->read_only_turn && !strncmp(c->first,"SAMERO VERIFY.",14)) {
            const char marker[]="Bookkeeping probe: PENDING_SERVER_CHECK.";
            char *p=strstr(c->first,marker);
            if (p) {
                const char *proof=c->access_verified?"Bookkeeping probe: READ_OK.":"Bookkeeping probe: NOT_VERIFIED.";
                size_t n=strlen(proof),old=sizeof(marker)-1;
                memmove(p+n,p+old,strlen(p+old)+1); memcpy(p,proof,n);
            }
        }
        if (!post_turn(m,l,c->first,&e)) log_system(m,l,e.msg);''')
edit('src/chat.c','''            const char *why="Codex đã từ chối thao tác. Máy chủ không gửi thêm lý do.";''','''            const char *why=l->read_only_turn?"BLOCKED_ACCESS: App Server ghi nhận thao tác bị từ chối trong lượt chỉ đọc.":"Codex đã từ chối thao tác. Máy chủ không gửi thêm lý do.";''')
edit('src/chat.c','''            char id[160], status[48];
            if (l->autonomous) {''','''            char id[160], status[48];
            if (l->autonomous && l->read_only_turn) {
                long long code=json_int(j,json_get(j,item,"exitCode"),-1);
                char state[48]={0}; json_field(j,item,"status",state,sizeof(state));
                if (code>0 || !strcmp(state,"failed")) {
                    char *out=allocate(TEXT_CAP+1);
                    if (json_field(j,item,"aggregatedOutput",out,TEXT_CAP+1) &&
                        (contains_ci(out,"Permission denied") || contains_ci(out,"Access is denied") ||
                         contains_ci(out,"UnauthorizedAccessException") || contains_ci(out,"denied by policy")))
                        c->observed_access_denial=1;
                    free(out);
                }
            }
            if (l->autonomous) {''')
edit('src/chat.c','const char *chat_runner_result(const Live *l) { return l->chat->runner_result.s; }','''const char *chat_runner_result(const Live *l) { return l->chat->runner_result.s; }
int chat_access_verified(const Live *l) { return l->chat && l->chat->access_verified; }
int chat_observed_access_denial(const Live *l) { return l->chat && l->chat->observed_access_denial; }''')
edit('src/manager.h','const char *chat_runner_result(const Live *);','''const char *chat_runner_result(const Live *);
int chat_access_verified(const Live *);
int chat_observed_access_denial(const Live *);''')
edit('src/runner.c','First use allowed read-only tools to inspect TASK_QUEUE.json, PROJECT_STATUS.md and required artifacts. If access is denied, return met:false, needsReview:true, evidence beginning BLOCKED_ACCESS: with denied path/tool.','Bookkeeping probe: PENDING_SERVER_CHECK. READ_OK proves only access to the two bookkeeping files, not acceptance. Use allowed read-only tools for required artifacts. Report BLOCKED_ACCESS: only with actual denial and path/tool; no tool result: BLOCKED_PREFLIGHT:.')
edit('src/runner.c','            Task *t=&r->tasks[r->index]; strcpy(t->evidence,evidence);','''            Task *t=&r->tasks[r->index];
            if (r->phase==VERIFY && !strcmp(review_blocker(evidence),"BLOCKED_ACCESS") && !chat_observed_access_denial(l)) {
                task_error(r,evidence);
                sam_format(evidence,sizeof(evidence),"BLOCKED_PREFLIGHT: Codex báo bị chặn nhưng chưa ghi nhận từ chối quyền từ công cụ. %s Chưa đủ bằng chứng nghiệm thu; giữ nguyên checkpoint.",
                    chat_access_verified(l)?"App Server đã đọc được hai tệp quản lý trong sandbox chỉ đọc.":"Kiểm tra đọc qua App Server chưa xác nhận được.");
            }
            strcpy(t->evidence,evidence);''')
# Tests are synthetic App Server messages; no live authenticated claim.
edit('tests/integration.py','''                if phase=="VERIFY" and (home/"blocked-access").exists():
                    response={"met":False,"needsReview":True,"evidence":"BLOCKED_ACCESS: read-only fixture cannot read required evidence."}''','''                if phase=="VERIFY" and (home/"blocked-access").exists():
                    expected="NOT_VERIFIED" if (home/"preflight-unsupported").exists() else "READ_OK"
                    assert "Bookkeeping probe: "+expected+"." in text
                    if (home/"observed-denial").exists() or (home/"unrelated-failure").exists():
                        out="Permission denied: required-artifact.json" if (home/"observed-denial").exists() else "File not found: optional-artifact.json"
                        event("item/completed",turnId=active,item={"id":active+"-failed","type":"commandExecution","command":"fixture-read","status":"failed","exitCode":1,"aggregatedOutput":out})
                    response={"met":False,"needsReview":True,"evidence":"BLOCKED_ACCESS: read-only fixture cannot read required evidence."}''')
edit('tests/integration.py','''        self.assertEqual((r["index"],r["phase"],r["blocker"]),(0,"verify","BLOCKED_ACCESS"))
        self.assertFalse(r["tasks"][0]["verifySession"])

    def test_resume_access_blocker_reuses_matching_test''','''        self.assertEqual((r["index"],r["phase"],r["blocker"]),(0,"verify","BLOCKED_PREFLIGHT"))
        self.assertFalse(r["tasks"][0]["verifySession"])
        self.assertIn("chưa xác nhận",r["reason"])

    def test_resume_access_blocker_reuses_matching_test''')
edit('tests/integration.py','''        self.assertEqual((r["index"],r["blocker"],r["tasks"][0]["reviewProbe"]),(0,"BLOCKED_ACCESS",0))''','''        self.assertEqual((r["index"],r["blocker"],r["tasks"][0]["reviewProbe"]),(0,"BLOCKED_PREFLIGHT",0))
        self.assertIn("App Server đã đọc được",r["reason"])''')
edit('tests/integration.py','    def test_reported_resource_blocker_never_passes(self):','''    def test_unrelated_command_failure_does_not_confirm_access_denial(self):
        cmd=self.runner_fixture(); home=self.root/"Autonomous"; (home/"blocked-access").touch(); (home/"unrelated-failure").touch()
        rid=self.req("runner-start",cmd)["id"]
        r=self.run_state(rid,lambda r:r["mode"]=="review" and not r["snapshot"])
        self.assertEqual((r["index"],r["blocker"]),(0,"BLOCKED_PREFLIGHT"))
        self.assertFalse(r["tasks"][0]["verifySession"])

    def test_actual_command_denial_remains_blocked(self):
        cmd=self.runner_fixture(); home=self.root/"Autonomous"; (home/"blocked-access").touch(); (home/"observed-denial").touch()
        rid=self.req("runner-start",cmd)["id"]
        r=self.run_state(rid,lambda r:r["mode"]=="review" and not r["snapshot"])
        self.assertEqual((r["index"],r["blocker"]),(0,"BLOCKED_ACCESS"))
        self.assertFalse(r["tasks"][0]["verifySession"])

    def test_reported_resource_blocker_never_passes(self):''')
print('PASS: scoped VERIFY proof and denial classification; sandbox and receipts unchanged')
