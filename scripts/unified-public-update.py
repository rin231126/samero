from pathlib import Path
import sys, os
os.chdir(Path(sys.argv[1]).resolve())
def replace(path,old,new):
    p=Path(path);s=p.read_text(encoding='utf-8')
    assert s.count(old)==1,(path,old[:80],s.count(old))
    p.write_text(s.replace(old,new),encoding='utf-8')
def add(path,content):
    p=Path(path);assert not p.exists(),path;p.write_text(content,encoding='utf-8')
add('src/update.c',r'''#include "manager.h"

/* The public channel is deliberately fixed. No project data or credentials
 * are sent and server-provided URLs are never followed. */
#define PUBLIC_UPDATE_URL "https://rin231126.github.io/samero/downloads/SAMERO-1.0.0-rc1.exe"
#ifndef SAM_RELEASE_SEQUENCE
#define SAM_RELEASE_SEQUENCE 0
#endif
static int hash_valid(const char *s) { return strlen(s)==64 && strspn(s,"0123456789abcdef")==64; }
int public_update_parse(const char *body,size_t size,long long current,Buf *out,Error *e) {
    JSON j;
    if (!size || size>4096 || !json_parse(&j,body,size)) return errorf(e,"Thông tin cập nhật không hợp lệ.");
    char channel[24],version[32],digest[65];
    int fields=ARG(&j,"channel",channel) && ARG(&j,"version",version) && ARG(&j,"sha256",digest);
    long long seq=NUMBER(&j,"sequence",-1), bytes=NUMBER(&j,"bytes",-1);
    int ok=fields && j.t[0].type=='{' && NUMBER(&j,"schema",-1)==1 && !strcmp(channel,"public") && !strcmp(version,SAM_VERSION) && hash_valid(digest) && seq>0 && seq<2147483648LL && bytes>0 && bytes<=64*MIB;
    json_free(&j);
    if (!ok) return errorf(e,"Thông tin cập nhật không đúng kênh Public 1.0.");
    buffer_char(out,'{'); json_pair(out,"status",seq>current?"available":"current");
    NUM(out,"currentSequence",current); NUM(out,"sequence",seq); NUM(out,"bytes",bytes); KEY(out,"sha256",digest); KEY(out,"url",PUBLIC_UPDATE_URL); buffer_char(out,'}');
    return 1;
}
#ifdef SAM_WINDOWS
typedef void *Http;
typedef unsigned short W;
typedef uint32_t DW;
extern Http WinHttpOpen(const W *,DW,const W *,const W *,DW);
extern Http WinHttpConnect(Http,const W *,unsigned short,DW);
extern Http WinHttpOpenRequest(Http,const W *,const W *,const W *,const W *,const W *const *,DW);
extern int WinHttpSetTimeouts(Http,int,int,int,int);
extern int WinHttpSetOption(Http,DW,void *,DW);
extern int WinHttpSendRequest(Http,const W *,DW,void *,DW,DW,uintptr_t);
extern int WinHttpReceiveResponse(Http,void *);
extern int WinHttpQueryHeaders(Http,DW,const W *,void *,DW *,DW *);
extern int WinHttpReadData(Http,void *,DW,DW *);
extern int WinHttpCloseHandle(Http);
#endif
int public_update_check(Buf *out,Error *e) {
#ifdef SAM_WINDOWS
    Http session=WinHttpOpen((const W *)L"SAMERO Public 1.0",0,NULL,NULL,0),connect=NULL,request=NULL;
    Buf body={0}; int ok=0;
    DW redirect=0,status=0,len=sizeof(status),n=0;
    char chunk[512];
    if (!session || !WinHttpSetTimeouts(session,5000,5000,5000,5000)) goto done;
    connect=WinHttpConnect(session,(const W *)L"rin231126.github.io",443,0);
    if (!connect) goto done;
    request=WinHttpOpenRequest(connect,(const W *)L"GET",(const W *)L"/samero/downloads/public-update.json",NULL,NULL,NULL,0x00800000);
    /* WINHTTP_OPTION_REDIRECT_POLICY=88, NEVER=0; never turn off TLS verification. */
    if (!request || !WinHttpSetOption(request,88,&redirect,sizeof(redirect))) goto done;
    if (!WinHttpSendRequest(request,NULL,0,NULL,0,0,0) || !WinHttpReceiveResponse(request,NULL)) goto done;
    if (!WinHttpQueryHeaders(request,19|0x20000000,NULL,&status,&len,NULL) || status!=200) goto done;
    do {
        if (!WinHttpReadData(request,chunk,sizeof(chunk),&n) || n>sizeof(chunk) || body.n+n>4096) goto done;
        if (n) buffer_add(&body,chunk,n);
    } while (n);
    ok=public_update_parse(body.s,body.n,SAM_RELEASE_SEQUENCE,out,e);
done:
    if (request) WinHttpCloseHandle(request);
    if (connect) WinHttpCloseHandle(connect);
    if (session) WinHttpCloseHandle(session);
    buffer_free(&body);
    if (!ok && !e->msg[0]) errorf(e,"Không kiểm tra được bản cập nhật qua HTTPS.");
    return ok;
#else
    (void)out;
    return errorf(e,"Kiểm tra cập nhật Public chỉ hỗ trợ Windows.");
#endif
}
''')
replace('src/manager.h','typedef struct Chat Chat;','int public_update_check(Buf *out,Error *e);\nint public_update_parse(const char *body,size_t size,long long current,Buf *out,Error *e);\ntypedef struct Chat Chat;')
p=Path('tools/imports.txt')
assert 'winhttp ' not in p.read_text()
p.write_text(p.read_text()+'winhttp WinHttpOpen WinHttpConnect WinHttpOpenRequest WinHttpSetTimeouts WinHttpSetOption WinHttpSendRequest WinHttpReceiveResponse WinHttpQueryHeaders WinHttpReadData WinHttpCloseHandle\n')
replace('tools/build.py','        flags.append(\'-DSAM_BUILD_ID=', '''        sequence = int(os.environ.get("GITHUB_RUN_NUMBER", "0"))
        if not 0 <= sequence < 2**31: raise ValueError("Invalid release sequence")
        flags.append(f"-DSAM_RELEASE_SEQUENCE={sequence}")
        flags.append('-DSAM_BUILD_ID=''')
replace('src/main.c','static const char *worker_argument(const char *action) {\n','static const char *worker_argument(const char *action) {\n    if (!strcmp(action,"public-update-check")) return "update";\n')
replace('src/main.c','    int picking=!strcmp(action,"pick");','    int picking=!strcmp(action,"pick"), updating=!strcmp(action,"public-update-check");')
replace('src/main.c','    if (!picking && !valid_id(id))','    if (!picking && !updating && !valid_id(id))')
replace('src/main.c','picking?p[1].p:id,YES(input','picking?p[1].p:updating?"public":id,YES(input')
replace('src/main.c','w->deadline=picking?0:monotonic_ms()+90000;','w->deadline=picking?0:monotonic_ms()+(updating?30000:90000);')
replace('src/main.c','    if (!field) return 1;\n    Manager *m=', '''    if (!field) return 1;
    if (!strcmp(action,"public-update-check")) {
        Buf result={0}; Error e={0};
        if (!public_update_check(&result,&e)) { buffer_char(&result,'{'); json_pair(&result,"error",e.msg); buffer_char(&result,'}'); }
        int ok=worker_stdout(result.s,result.n); buffer_free(&result); return !ok;
    }
    Manager *m=''')
replace('web/index.html','      <div id="feedback"', '''      <section id="public-update-banner" class="card" hidden aria-live="polite">
        <div class="section-head"><h2>SAMERO Public · Cập nhật</h2><button id="public-update-close" class="quiet" type="button">Đóng</button></div>
        <p id="public-update-message"></p><div class="actions"><a id="public-update-download" href="https://rin231126.github.io/samero/downloads/SAMERO-1.0.0-rc1.exe" target="_blank" rel="noopener noreferrer" hidden>Tải EXE chính thức</a><button id="public-update-retry" type="button">Kiểm tra lại</button></div>
        <small id="public-update-sha"></small>
      </section>
      <div id="feedback"''')
replace('web/index.html','<button id="refresh"','<button id="public-update-check" class="quiet" type="button">Cập nhật</button>\n        <button id="refresh"')
replace('web/app.js','mountUiLifetime();\nSameroStudio.mount();',r'''// The public channel only announces verified CI releases; it never runs a remote EXE.
function mountPublicUpdate() {
  const banner=$("#public-update-banner"), message=$("#public-update-message"), link=$("#public-update-download"), digest=$("#public-update-sha");
  if (!banner || !message || !link || !digest) return;
  let checking=false, dismissed=0;
  async function check(manual=false) {
    if (checking || document.hidden) return;
    checking=true;
    if (manual) { banner.hidden=false; message.textContent="Đang kiểm tra bản phát hành…"; link.hidden=true; digest.textContent=""; }
    try {
      const r=await api("public-update-check");
      if (r.status==="available" && Number.isSafeInteger(r.sequence) && r.sequence>r.currentSequence && /^[a-f0-9]{64}$/.test(r.sha256)) {
        if (!manual && dismissed===r.sequence) return;
        banner.dataset.sequence=String(r.sequence); banner.hidden=false;
        message.textContent=`Có bản dựng mới 1.0 (#${r.sequence}). Tải bản mới, kiểm tra SHA-256 và đóng Manager cũ khi không còn tác vụ đang chạy.`;
        link.hidden=false; digest.textContent=`SHA-256: ${r.sha256}`;
      } else { link.hidden=true; digest.textContent=""; banner.dataset.sequence="0"; if (manual) message.textContent="Không có bản dựng mới hơn."; else banner.hidden=true; }
    } catch (error) { if (manual) { message.textContent=error.message; link.hidden=true; digest.textContent=""; } }
    finally { checking=false; }
  }
  $("#public-update-check")?.addEventListener("click",()=>check(true));
  $("#public-update-retry")?.addEventListener("click",()=>check(true));
  $("#public-update-close")?.addEventListener("click",()=>{ dismissed=Number(banner.dataset.sequence)||0; banner.hidden=true; });
  if (typeof setTimeout==="function") setTimeout(()=>check(),5000);
  setInterval(()=>check(),15*60*1000);
}
mountUiLifetime();
mountPublicUpdate();
SameroStudio.mount();''')
add('tests/update-manifest.c',r'''#include "../src/manager.h"
#include <assert.h>
static const char *sha="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
static void check(const char *channel,long long sequence,long long current,const char *version,const char *digest,long long size,int ok,const char *status) {
    char body[512],actual[32]; Buf out={0}; Error e={0};
    int n=sam_format(body,sizeof(body),"{\"schema\":1,\"channel\":\"%s\",\"version\":\"%s\",\"sequence\":%lld,\"sha256\":\"%s\",\"bytes\":%lld,\"url\":\"https://untrusted.invalid/evil.exe\"}",channel,version,sequence,digest,size);
    assert(n>0 && n<(int)sizeof(body));
    assert(public_update_parse(body,(size_t)n,current,&out,&e)==ok);
    if(ok) { JSON j; assert(json_parse(&j,out.s,out.n)); ARG(&j,"status",actual); assert(!strcmp(actual,status)); assert(!strstr(out.s,"untrusted.invalid")); json_free(&j); }
    else assert(e.msg[0] && !out.n);
    buffer_free(&out);
}
int main(void) {
    check("public",11,10,SAM_VERSION,sha,1000,1,"available");
    check("public",10,10,SAM_VERSION,sha,1000,1,"current");
    check("public",9,10,SAM_VERSION,sha,1000,1,"current");
    check("developer",11,10,SAM_VERSION,sha,1000,0,"");
    check("public",11,10,"1.1",sha,1000,0,"");
    check("public",11,10,SAM_VERSION,"bad",1000,0,"");
    check("public",11,10,SAM_VERSION,sha,0,0,"");
    check("public",11,10,SAM_VERSION,sha,64*MIB+1,0,"");
    check("public",-1,10,SAM_VERSION,sha,1000,0,"");
    puts("PASS: 9 manifest cases; fixed update URL; downgrade not offered");
}
''')
add('tests/update-ui.cjs',r'''const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const app=fs.readFileSync(require('node:path').join(__dirname,'../web/app.js'),'utf8');
const code=app.slice(app.indexOf('function mountPublicUpdate()'),app.indexOf('\nmountUiLifetime();',app.indexOf('function mountPublicUpdate()')));
const nodes=new Map();
const node=s=>{if(!nodes.has(s))nodes.set(s,{hidden:true,dataset:{},textContent:'',addEventListener(event,cb){this[event]=cb}});return nodes.get(s)};
const digest='a'.repeat(64); let result={status:'available',sequence:2,currentSequence:1,sha256:digest}; let calls=0,initial,poll;
const ctx={$:node,document:{hidden:false},api:async()=>{calls++; if(result instanceof Error)throw result;return result},setTimeout:fn=>{initial=fn},setInterval:fn=>{poll=fn}};
vm.runInNewContext(code+'\nmountPublicUpdate();',ctx);
(async()=>{
 const banner=node('#public-update-banner'),link=node('#public-update-download'),message=node('#public-update-message');
 await initial(); assert.equal(banner.hidden,false);assert.equal(link.hidden,false);assert.match(message.textContent,/#2/);
 node('#public-update-close').click();await poll();assert.equal(banner.hidden,true);
 result={...result,sequence:3};await poll();assert.equal(banner.hidden,false);assert.match(message.textContent,/#3/);
 result={status:'current',sequence:1,currentSequence:1,sha256:digest};await poll();assert.equal(banner.hidden,true);assert.equal(link.hidden,true);
 result=new Error('Offline');await node('#public-update-check').click();assert.equal(banner.hidden,false);assert.equal(link.hidden,true);assert.equal(message.textContent,'Offline');
 ctx.document.hidden=true;const before=calls;await poll();assert.equal(calls,before);
 console.log('PASS: public update notification, dismissal, newer release, downgrade, offline, hidden window');
})().catch(e=>{console.error(e);process.exitCode=1});
''')
print('PASS: public update notification and parser source')
