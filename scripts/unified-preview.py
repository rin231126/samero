from pathlib import Path
from playwright.sync_api import sync_playwright
from urllib.request import urlopen
import sys,tempfile,subprocess,time,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
WORK=ROOT/'release-work'
APP=WORK/'app'
exe=Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix='samero-preview-') as td:
    data=Path(td)/'data'
    child=subprocess.Popen([str(exe),'--headless','--data-dir',str(data)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        end=time.monotonic()+15
        while not (data/'ui.url').is_file() or not (data/'ui.version').is_file():
            assert time.monotonic()<end and child.poll() is None
            time.sleep(.1)
        url=(data/'ui.url').read_text()
        origin=url.split('/#')[0]
        out=WORK/'preview';out.mkdir(exist_ok=True)
        for name in ['normal','open','office-owl','office-beaver','office-cat','office-wolf','office-rabbit','office-penguin']:
            raw=urlopen(origin+'/mascot/'+name+'.png',timeout=5).read()
            assert raw==(APP/'web/mascot'/f'{name}.png').read_bytes(),name
        assert urlopen(origin+'/favicon.ico',timeout=5).read()==(APP/'web/samero.ico').read_bytes()
        with sync_playwright() as p:
            browser=p.chromium.launch(channel='chrome',headless=True,chromium_sandbox=True)
            page=browser.new_page(viewport={'width':1500,'height':925},color_scheme='dark',reduced_motion='reduce')
            errors=[];bad=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('response',lambda r:bad.append((r.status,r.url)) if r.status>=400 else None)
            page.goto(url,wait_until='domcontentloaded')
            # The current release starts on Workspace, whose rendered root is
            # .chat-grid, not .hero. Wait for the real state-driven view.
            page.wait_for_selector('#content .chat-grid', timeout=30000)
            assert page.locator('body').get_attribute('data-page') == 'chat'
            page.locator('button[data-page=studio]').click()
            page.wait_for_selector('#content .studio-hero', timeout=30000)
            assert page.locator('body').get_attribute('data-page') == 'studio'
            page.wait_for_selector('.office-station img')
            assert page.locator('.office-station').count()==7
            page.locator('[data-studio-theme=ocean]').click()
            page.wait_for_function("document.documentElement.dataset.palette === 'ocean'")
            page.wait_for_function("Array.from(document.querySelectorAll('.office-station img')).every(i=>i.complete&&i.naturalWidth===48)")
            page.evaluate('window.scrollTo(0,0)')
            page.screenshot(path=str(out/'studio-top.png'),animations='disabled')
            page.screenshot(path=str(out/'studio.png'),full_page=True,animations='disabled')
            page.locator('.pixel-office').screenshot(path=str(out/'office.png'),animations='disabled')
            page.locator('.studio-settings').screenshot(path=str(out/'settings.png'),animations='disabled')
            page.locator('#mascot-toggle').click()
            assert page.locator('#mascot-image').get_attribute('src')=='/mascot/open.png'
            page.locator('#mascot-toggle').click()
            page.locator('[data-studio-theme=midnight]').click()
            page.wait_for_function("document.documentElement.dataset.palette === 'midnight'")
            page.evaluate('window.scrollTo(0,0)')
            page.screenshot(path=str(out/'studio-purple.png'),animations='disabled')
            page.locator('[data-studio-theme=ocean]').click()
            for w,h in [(1500,925),(1280,720),(1024,768),(700,720),(560,800)]:
                page.set_viewport_size({'width':w,'height':h})
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),('app horizontal overflow',w)
                assert page.locator('.office-station').count()==7
            assert not errors,errors
            assert not bad,bad
            browser.close()
    finally:
        child.terminate()
        try: child.wait(timeout=10)
        except subprocess.TimeoutExpired: child.kill();child.wait()
print('PASS: actual running Manager, exact embedded favicon and eight sprites, logo interaction, themes, 5 app viewport sizes')
