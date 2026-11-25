from pathlib import Path
import sys
APP=Path(sys.argv[1]).resolve()
def change(name,old,new):
 p=APP/name;s=p.read_text(encoding='utf-8');assert s.count(old)==1,(name,old[:80]);p.write_text(s.replace(old,new),encoding='utf-8')
change('src/manager.h','int runner_checkpoint_busy(Manager *);','int runner_checkpoint_busy(Manager *);\nint runner_pending_work(Manager *);')
change('src/runner.c','void runner_free(Manager *m) {','''int runner_pending_work(Manager *m) {
    for (Run *r=m->runs;r;r=r->next) if (!r->retired &&
        (r->archiver.handle || r->snapshot || r->inflight || r->mode==ACTIVE ||
         (r->mode==LIMITED && r->auto_resume))) return 1;
    return 0;
}
void runner_free(Manager *m) {''')
change('src/main.c','static ReadWorker workers[3];','''static ReadWorker workers[3];
/* Browser windows are not owned processes. Use authenticated, per-page leases. */
static struct { char id[33]; uint64_t until; } ui_leases[32];
static uint64_t ui_start_until;
static int ui_lease(const JSON *input) {
    char id[33]; ARG(input,"id",id);
    if (!valid_id(id)) return 0;
    uint64_t now=monotonic_ms(); int slot=-1;
    for (size_t i=0;i<ARRAY_LEN(ui_leases);++i) {
        if (!strcmp(ui_leases[i].id,id)) { slot=(int)i; break; }
        if (slot<0 && ui_leases[i].until<=now) slot=(int)i;
    }
    if (slot<0) return 0;
    strcpy(ui_leases[slot].id,id);
    ui_leases[slot].until=now+(YES(input,"closing")?15000u:180000u);
    ui_start_until=0;
    return 1;
}
static int ui_attached(void) {
    uint64_t now=monotonic_ms();
    if (now<ui_start_until) return 1;
    for (size_t i=0;i<ARRAY_LEN(ui_leases);++i) if (ui_leases[i].until>now) return 1;
    return 0;
}''')
change('src/main.c','    if (!strcmp(action,"account-refresh") && chat_quota_refresh(m,requested_profile)) {','''    if (!strcmp(action,"ui-lease")) {
        if (ui_lease(&input)) response(fd,200,"application/json; charset=utf-8","{}",2);
        else send_error(fd,409,"Không nhận được định danh giao diện hợp lệ.");
    } else if (!strcmp(action,"account-refresh") && chat_quota_refresh(m,requested_profile)) {''')
change('src/main.c','    if (!headless && !open_url(url,1)) {','    ui_start_until=monotonic_ms()+120000u;\n    if (!headless && !open_url(url,1)) {')
change('src/main.c','        quota_tick(m);\n        runner_tick(m);','''        runner_tick(m);
        /* Never interrupt a write, checkpoint or active Codex on UI loss. */
        if (!headless && !ui_attached() && !m->live && !runner_pending_work(m) && !m->runner_fault) {
            m->quit=1; break;
        }
        quota_tick(m);''')
change('src/main.c','        process_stop(&workers[i].process); process_dispose(&workers[i].process); buffer_free(&workers[i].data);','''        process_stop(&workers[i].process); process_dispose(&workers[i].process);
        if (workers[i].client!=BAD_SOCKET) socket_close(workers[i].client);
        buffer_free(&workers[i].data);''')
change('web/app.js','function notify(text = "", type = "") {','''function mountUiLifetime() {
  if (!/^[a-f0-9]{32}$/.test(key) || typeof crypto === "undefined" || !crypto.getRandomValues) return;
  const id=Array.from(crypto.getRandomValues(new Uint8Array(16)),b=>b.toString(16).padStart(2,"0")).join("");
  const pulse=()=>api("ui-lease",{id}).catch(()=>{});
  pulse(); setInterval(pulse,10000);
  window.addEventListener("pageshow",pulse);
  document.addEventListener("visibilitychange",()=>{ if (!document.hidden) pulse(); });
  window.addEventListener("pagehide",()=>{
    fetch("/api/ui-lease",{method:"POST",headers:{"Content-Type":"application/json","X-Samero-Key":key},body:JSON.stringify({id,closing:true}),keepalive:true}).catch(()=>{});
  });
  window.addEventListener("beforeunload",event=>{
    if (data?.sessions?.some(live) || data?.runs?.some(r=>["active","quota"].includes(r.mode))) {
      event.preventDefault(); event.returnValue="";
    }
  });
}
function notify(text = "", type = "") {''')
change('web/app.js','    button("Thoát Manager","exit","","danger")) +','''    button("Thoát Manager","exit","","danger")) +
    `<section class="card"><strong>Thoát hoàn toàn</strong><p>Đóng mọi cửa sổ Manager sẽ tự dừng ứng dụng khi rảnh (có thời gian chờ để tránh ngắt khi tải lại). Nếu còn nhiệm vụ hoặc phiên Codex đang chạy, hãy STOP/đóng phiên, chờ checkpoint và bấm Thoát Manager. Không tự tắt Edge hay phiên ngoài Manager.</p></section>` +''')
change('web/app.js','SameroStudio.mount();','mountUiLifetime();\nSameroStudio.mount();')
