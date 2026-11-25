from pathlib import Path
import sys, os
os.chdir(Path(sys.argv[1]).resolve())
def replace(path, old, new):
    p=Path(path); s=p.read_text(encoding='utf-8'); assert s.count(old)==1,(path,old[:90],s.count(old)); p.write_text(s.replace(old,new),encoding='utf-8')
replace('src/base.h','int file_info(const char *path, Info *info);','int file_info(const char *path, Info *info);\nconst char *probe_read_regular(const char *path, unsigned *code);')
replace('src/platform.c','int list_dir_filtered(const char *dir, NameFilter filter, Visitor cb, void *ctx, Error *e) {\n    Path *glob', '''/* Local OS access probe: no content returned, no reparse traversal. */
const char *probe_read_regular(const char *path, unsigned *code) {
    *code=0;
    W *name=file_wide(path);
    if (!name) return "INVALID_PATH";
    H h=CreateFileW(name,0x80000000,7,NULL,3,0x00200000,NULL);
    DW err=h==INVALID?GetLastError():0;
    free(name);
    if (h==INVALID) { *code=err; return err==2 || err==3?"MISSING":err==5?"DENIED":err==32 || err==33?"BUSY":"OPEN_FAILED"; }
    HandleInfo st;
    const char *status="OK";
    unsigned char b; DW n=0;
    if (!GetFileInformationByHandle(h,&st)) { *code=GetLastError(); status="STAT_FAILED"; }
    else if (st.attributes & 0x410) status="UNSAFE_TYPE";
    else if (!ReadFile(h,&b,1,&n,NULL)) { *code=GetLastError(); status="READ_FAILED"; }
    CloseHandle(h);
    return status;
}
int list_dir_filtered(const char *dir, NameFilter filter, Visitor cb, void *ctx, Error *e) {
    Path *glob''')
replace('src/platform.c','int list_dir_filtered(const char *dir, NameFilter filter, Visitor cb, void *ctx, Error *e) {\n    DIR *d', '''const char *probe_read_regular(const char *path, unsigned *code) {
    *code=0;
    int fd=open(path,O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC);
    if (fd<0) { int err=errno; *code=(unsigned)err; return err==ENOENT || err==ENOTDIR?"MISSING":err==EACCES || err==EPERM?"DENIED":err==ELOOP?"UNSAFE_TYPE":"OPEN_FAILED"; }
    struct stat st; unsigned char b;
    const char *status="OK";
    if (fstat(fd,&st)) { *code=(unsigned)errno; status="STAT_FAILED"; }
    else if (!S_ISREG(st.st_mode)) status="UNSAFE_TYPE";
    else if (read(fd,&b,1)<0) { *code=(unsigned)errno; status="READ_FAILED"; }
    close(fd);
    return status;
}
int list_dir_filtered(const char *dir, NameFilter filter, Visitor cb, void *ctx, Error *e) {
    DIR *d''')
replace('src/runner.c','/* Hash the exact bytes parsed, and check their binding to the project and workspace.', '''/* Fixed bookkeeping files only; host access is not sandbox verification. */
static int local_access(Manager *m,const Run *r,Buf *out,Error *e) {
    Error binding={0}; int ok=bound(m,r,&binding), readable=ok;
    const char *names[]={"TASK_QUEUE.json","PROJECT_STATUS.md"};
    Path *p=allocate(sizeof(*p));
    if (out) { buffer_char(out,'{'); json_pair(out,"binding",ok?"OK":"INVALID"); RAW(out,"files","["); }
    for (size_t i=0;i<ARRAY_LEN(names);++i) {
        unsigned code=0;
        const char *status=!ok?"NOT_CHECKED":!path_join(p,r->workspace.p,names[i])?"INVALID_PATH":probe_read_regular(p->p,&code);
        if (strcmp(status,"OK")) { readable=0; if (e && !*e->msg) errorf(e,"Kiểm tra trên máy: %s — %s (OS %u). Mở Kiểm tra quyền; chưa chạy RESUME.",names[i],status,code); }
        if (out) { if (i) buffer_char(out,','); buffer_char(out,'{'); json_pair(out,"name",names[i]); KEY(out,"status",status); NUM(out,"osCode",code); buffer_char(out,'}'); }
    }
    free(p);
    if (out) { buffer_char(out,']'); RAW(out,"hostReadable",readable?"true":"false"); KEY(out,"codexBlocker",r->index<r->count?review_blocker(r->tasks[r->index].evidence):""); KEY(out,"codexReason",r->reason); NUM(out,"revision",r->revision); KEY(out,"buildId",SAM_BUILD_ID); buffer_char(out,'}'); }
    return readable;
}
/* Hash the exact bytes parsed, and check their binding to the project and workspace.''')
replace('src/runner.c','    int rev=json_get(in,0,"revision");','    if (!strcmp(action,"runner-access")) { local_access(m,r,out,NULL); return 1; }\n    int rev=json_get(in,0,"revision");')
replace('src/runner.c','        if (!bound(m,r,e) || !reconcile_queue(m,r,e)) return 0;\n        int migrated=', '''        if (r->phase==VERIFY && r->index<r->count) {
            const char *block=review_blocker(r->tasks[r->index].evidence);
            if ((!strcmp(block,"BLOCKED_ACCESS") || !strcmp(block,"BLOCKED_PREFLIGHT")) && !local_access(m,r,NULL,e)) return 0;
        }
        if (!bound(m,r,e) || !reconcile_queue(m,r,e)) return 0;
        int migrated=''')
replace('src/manager.h','#define SAM_VERSION "1.0.0-rc1"','#define SAM_VERSION "1.0.0-rc1"\n#ifndef SAM_BUILD_ID\n#define SAM_BUILD_ID "unidentified"\n#endif')
replace('src/main.c','const char prefix[]=SAM_VERSION "\\n";','const char prefix[]=SAM_VERSION "\\n" SAM_BUILD_ID "\\n";')
replace('src/main.c','"%s\\n%s",SAM_VERSION,url','"%s\\n%s\\n%s",SAM_VERSION,SAM_BUILD_ID,url')
replace('src/manager.c','    KEY(out,"version",SAM_VERSION);','    KEY(out,"version",SAM_VERSION); KEY(out,"buildId",SAM_BUILD_ID);')
replace('tools/build.py','import argparse\n','import argparse\nimport hashlib\n')
replace('tools/build.py','        if target == "linux":\n            run(os.environ', '''        digest = hashlib.sha256()
        for f in sorted([*sources, *(ROOT/'src').glob('*.h'), *[p for p in (ROOT/'web').rglob('*') if p.is_file()], Path(__file__).resolve()]):
            digest.update(f.relative_to(ROOT).as_posix().encode()+b'\\0'+hashlib.sha256(f.read_bytes()).digest())
        flags.append('-DSAM_BUILD_ID="'+digest.hexdigest()[:16]+'"')
        if target == "linux":
            run(os.environ''')
replace('web/app.js','        ${["review","blocked"].includes(r.mode)?button("Chẩn đoán","runner-diagnostic",r.id):""}', '''        ${["review","blocked"].includes(r.mode)?button("Chẩn đoán","runner-diagnostic",r.id):""}
        ${["BLOCKED_ACCESS","BLOCKED_PREFLIGHT"].includes(r.blocker)?button("Kiểm tra quyền","runner-access",r.id,"primary"):""}''')
replace('web/app.js','  return hero("Cài đặt", `SAMERO ${s.version || ""} · CLI, thư mục sao lưu và giao diện.`,','  return hero("Cài đặt", `SAMERO ${s.version || ""} · Build ${s.buildId || "cũ"} · CLI, thư mục sao lưu và giao diện.`,')
replace('web/app.js','  "runner-diagnostic": id=>{', '''  "runner-access": id=>{
    const r=byId(data.runs,id); if(!r)return;
    return run("Đang kiểm tra quyền đọc trên máy…",async()=>{
      const v=await api("runner-access",{project:r.project,id:r.id});
      const labels={OK:"Đọc được",MISSING:"Không tìm thấy",DENIED:"Từ chối quyền",BUSY:"Tệp đang bị khóa",UNSAFE_TYPE:"Loại tệp không an toàn",INVALID_PATH:"Đường dẫn lỗi",NOT_CHECKED:"Chưa kiểm tra"};
      const rows=v.files.map(f=>tr(html(f.name),html(labels[f.status]||f.status),String(f.osCode)));
      show("Kiểm tra quyền truy cập",`<p>Build ${html(v.buildId)} · Revision ${Number(v.revision)}</p>
        <p>Liên kết dự án/hồ sơ: ${html(v.binding)}</p>${table(["Tệp","Quyền đọc trên máy","Mã OS"],rows)}
        <p>${v.hostReadable?"Manager đọc được hai tệp bằng quyền Windows/Linux hiện tại. Điều này không chứng minh quyền đọc bên trong sandbox Codex.":"Manager chưa đọc được đầy đủ. Kiểm tra tệp, đường dẫn hoặc quyền hệ điều hành trước RESUME."}</p>
        <p>Trạng thái Codex gần nhất: ${html(v.codexBlocker||"Chưa xác định")} · ${html(v.codexReason||"")}</p>
        <p>Nếu Manager đọc được nhưng Codex bị chặn, xem nhật ký xét duyệt và cấu hình CLI của hồ sơ. Chỉ dùng quyền được phép; không tự nâng quyền. RESUME sẽ kiểm tra sandbox lại.</p>
        <div class="actions">${button("Mở Workspace","open-chat",r.project)}${button("Nhật ký xét duyệt","review-history",r.project)}</div>`);
      return "Đã kiểm tra quyền trên máy; không thay đổi tiến độ.";
    });
  },
  "runner-diagnostic": id=>{''')
replace('web/app.js','<textarea readonly rows="16" style="width:100%">${html(report)}</textarea>','<div class="actions">${button("Kiểm tra quyền trên máy","runner-access",r.id)}</div><textarea readonly rows="16" style="width:100%">${html(report)}</textarea>')
replace('web/app.js','const report=JSON.stringify({revision:r.revision,phase:r.phase','const report=JSON.stringify({buildId:data.settings.buildId||"legacy",revision:r.revision,phase:r.phase')
replace('tests/integration.py','f"{s[\'version\']}\\n{self.url}/#{self.key}"','f"{s[\'version\']}\\n{s[\'buildId\']}\\n{self.url}/#{self.key}"')
replace('tests/integration.py','        version.write_text(original)\n        same=subprocess.run(args', '''        version.write_text(original.replace(original.splitlines()[1],"old-build",1))
        old_build=subprocess.run(args,capture_output=True,text=True,timeout=5)
        self.assertEqual(old_build.returncode,1)
        self.assertFalse(old_build.stdout)
        version.write_text(original)
        same=subprocess.run(args''')
replace('tests/integration.py','    def test_preflight_unsupported_does_not_fake_verification(self):', '''    def test_local_access_diagnostics_are_read_only_and_distinguish_host_from_codex(self):
        cmd=self.runner_fixture();home=self.root/"Autonomous"; (home/"preflight-denied").touch()
        rid=self.req("runner-start",cmd)["id"];ctl={"project":cmd["project"],"id":rid,"confirmed":True}
        r=self.run_state(rid,lambda r:r["mode"]=="review" and not r["snapshot"])
        q=self.workspace/"TASK_QUEUE.json"; before=q.read_bytes()
        report=self.req("runner-access",ctl)
        self.assertTrue(report["hostReadable"]);self.assertEqual(report["codexBlocker"],"BLOCKED_ACCESS")
        self.assertEqual(report["revision"],r["revision"]);self.assertEqual(before,q.read_bytes())
        self.req("runner-access",ctl,key="bad",expected=403)
        q.unlink(); report=self.req("runner-access",ctl)
        self.assertFalse(report["hostReadable"]);self.assertEqual(report["files"][0]["status"],"MISSING")
        self.req("runner-resume",ctl,expected=409)
        self.assertEqual(self.run_state(rid)["revision"],r["revision"])
        if os.name!="nt":
            q.symlink_to(self.workspace/".env");report=self.req("runner-access",ctl)
            self.assertEqual(report["files"][0]["status"],"UNSAFE_TYPE");q.unlink()
        q.write_bytes(before)
        self.assertTrue(self.req("runner-access",ctl)["hostReadable"])

    def test_preflight_unsupported_does_not_fake_verification(self):''')
print('PASS: native read diagnostics and same-version build identity source patch')
