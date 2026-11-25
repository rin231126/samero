from pathlib import Path
from urllib.parse import urlparse, unquote
from html.parser import HTMLParser
from playwright.sync_api import sync_playwright
import contextlib, hashlib, http.server, os, threading, json, time

ROOT=Path(__file__).resolve().parent.parent
os.chdir(ROOT)
class Parse(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.refs=[]
    def handle_starttag(self,t,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        self.refs.extend(a[k] for k in ('src','href','poster','data-image') if k in a and a[k])
for page in ['index.html','en.html']:
    p=Parse();p.feed(Path(page).read_text())
    assert len(p.ids)==len(set(p.ids)),('duplicate id',page)
    for ref in p.refs:
        if ref.startswith('#'):assert ref[1:] in p.ids,(page,ref)
        elif not urlparse(ref).scheme:assert (ROOT/unquote(urlparse(ref).path)).is_file(),(page,ref)
for line in (ROOT/'downloads/SHA256SUMS-1.0.0-rc1.txt').read_text().splitlines():
    digest,name=line.split(maxsplit=1)
    assert hashlib.sha256((ROOT/'downloads'/name).read_bytes()).hexdigest()==digest
print('PASS: local links, anchor IDs, release hashes')
class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/'
os.makedirs('website-qa',exist_ok=True)
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True,args=['--no-sandbox'])
        for lang,file in [('vi','index.html'),('en','en.html')]:
            for width,height in [(1920,1080),(1440,900),(1366,768),(1024,768),(768,1024),(390,844),(320,740)]:
                ctx=browser.new_context(viewport={'width':width,'height':height},accept_downloads=True, reduced_motion='reduce')
                page=ctx.new_page();errors=[];failed=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('response',lambda r:failed.append((r.status,r.url)) if r.status>=400 else None)
                page.goto(url+file,wait_until='load')
                assert page.locator('link[rel=icon][type="image/x-icon"]').get_attribute('href')=='assets/brand-1.0.ico'
                assert page.request.get(url+'assets/brand-1.0.ico').status==200
                assert page.request.get(url+'favicon.ico').status==200
                page.wait_for_function('document.querySelector("#film").readyState >= 1',timeout=30000)
                assert page.locator('html').get_attribute('lang')==lang
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),(lang,width,'horizontal overflow')
                if page.locator('#mascot').is_visible():
                    page.locator('#mascot').click()
                    assert page.locator('#mascot-img').get_attribute('src')=='assets/brand-1.0-open.png'
                    page.locator('#mascot').click()
                    assert page.locator('#mascot-img').get_attribute('src')=='assets/brand-1.0-normal.png'
                if width<=920:
                    page.locator('.mobile summary').click()
                    assert page.locator('.mobile').get_attribute('open') is not None
                    page.locator('.mobile a').first.click()
                    assert page.locator('.mobile').get_attribute('open') is None
                for b in page.locator('.tab').all():
                    b.click()
                    assert b.get_attribute('aria-pressed')=='true'
                    assert page.locator('#demo-img').get_attribute('src')==b.get_attribute('data-image')
                    page.wait_for_function('document.querySelector("#demo-img").complete && document.querySelector("#demo-img").naturalWidth > 0')
                for b in page.locator('.theme').all():
                    b.click()
                    assert page.locator('body').get_attribute('data-theme')==b.get_attribute('data-theme')
                page.locator('.theme[data-theme=ocean]').click()
                page.locator('#copy').click()
                page.wait_for_function('document.querySelector("#copy-result").textContent.length > 0')
                # Force lazy images into view; verify decoding for every image.
                page.evaluate("Array.from(document.images).forEach(i=>i.loading='eager')")
                for im in page.locator('img').all():
                    if im.is_visible():im.scroll_into_view_if_needed(timeout=5000)
                page.wait_for_function('Array.from(document.images).every(i=>i.complete && i.naturalWidth>0)')
                if width==1440:
                    page.locator('#play').click()
                    page.wait_for_function('document.querySelector("#film").currentTime > .1',timeout=20000)
                    page.locator('#film').evaluate('(v)=>v.pause()')
                    for name in ['SAMERO-1.0.0-rc1.exe','SAMERO-1.0.0-rc1-Portable.zip','SAMERO-1.0.0-rc1-Source.zip']:
                        with page.expect_download() as dl:page.locator('a[href="downloads/'+name+'"]').click()
                        assert hashlib.sha256(dl.value.path().read_bytes()).digest()==hashlib.sha256(Path('downloads',name).read_bytes()).digest()
                page.evaluate('window.scrollTo(0,0)')
                page.screenshot(path=f'website-qa/{lang}-{width}.png',full_page=True,animations='disabled')
                assert not errors,(lang,width,errors)
                assert not failed,(lang,width,failed)
                print(f'PASS {lang} {width}px: layout, media, controls, links')
                ctx.close()
        browser.close()
finally:server.shutdown()
print('PASS: all fourteen Chromium browser cases; downloads verified byte-for-byte')
