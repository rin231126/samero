from pathlib import Path
from PIL import Image, ImageOps
import hashlib, zipfile, shutil, re
ROOT=Path(__file__).resolve().parent.parent
WORK=ROOT/'release-work';APP=WORK/'app';A=ROOT/'assets';D=ROOT/'downloads'
exe=WORK/'SAMERO-1.0.0-rc1.exe'
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=f"""SAMERO 1.0.0-rc1 — first public release candidate
EXE SHA-256: {digest(exe)}
Windows 10/11 x64. Unsigned release candidate; not an official OpenAI product.
Verified in this publishing workflow:
- Linux and Windows x64 builds; PE and seven icon resource checks.
- Seven JavaScript unit suites, three audio decode checks.
- Local Bridge and Continuous Development integration tests.
- Actual Linux Chrome Manager and embedded asset bytes; five viewport sizes.
- Native Windows isolated smoke test: startup, workspace/profile management, bridge, checkpoint/restore.
The app's six role sprites, original logo, screenshots, video and downloads are generated from this same source archive.
Not verified: authenticated live Codex operation, audio hardware, all Windows desktop configurations. See workflow logs for full regression results.
"""
(APP/'TEST-RESULTS.txt').write_text(report)
(D/'TEST-RESULTS-1.0.0-rc1.txt').write_text(report)
shutil.copyfile(exe,D/exe.name)
source=D/'SAMERO-1.0.0-rc1-Source.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for f in sorted(APP.rglob('*')):
        if f.is_file() and '__pycache__' not in f.parts and not f.name.endswith('.pyc'):
            z.write(f,f.relative_to(APP))
portable=D/'SAMERO-1.0.0-rc1-Portable.zip'
with zipfile.ZipFile(portable,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    files={exe.name:exe,'HUONG-DAN.txt':APP/'HUONG-DAN-PORTABLE.txt','TEST-RESULTS.txt':APP/'TEST-RESULTS.txt','SAMERO.ico':APP/'web/samero.ico',**{str(f.relative_to(APP)):f for f in (APP/'extension').glob('*') if f.is_file()}}
    for n,p in files.items():z.write(p,n)
    z.writestr('SHA256SUMS.txt',''.join(f'{digest(p)}  {n}\n' for n,p in files.items()))
    assert z.read(exe.name)==exe.read_bytes()
downloads=[D/exe.name,portable,source,D/'TEST-RESULTS-1.0.0-rc1.txt']
(D/'SHA256SUMS-1.0.0-rc1.txt').write_text(''.join(f'{digest(p)}  {p.name}\n' for p in downloads))
for name in ['normal','open']:
    shutil.copyfile(APP/'web/mascot'/f'{name}.png',A/f'{name}.png')
    shutil.copyfile(APP/'web/mascot'/f'{name}.png',A/f'brand-1.0-{name}.png')
for name in ['owl','beaver','cat','wolf','rabbit','penguin']:
    shutil.copyfile(APP/'web/mascot'/f'office-{name}.png',A/f'launch-{name}.png')
    shutil.copyfile(APP/'web/mascot'/f'office-{name}.png',A/f'crew-1.0-{name}.png')
shutil.copyfile(APP/'web/samero.ico',ROOT/'favicon.ico')
shutil.copyfile(APP/'web/samero.ico',A/'brand-1.0.ico')
for name in ['studio-top.png','studio.png','office.png','settings.png','studio-purple.png']:
    shutil.copyfile(WORK/'preview'/name,A/name)
for lang,filename in [('vi','index.html'),('en','en.html')]:
    s=(ROOT/'scripts'/f'site-v1-{lang}.html').read_text()
    s=s.replace('assets/normal.png','assets/brand-1.0-normal.png').replace('site-v1.css','site-1.0.0.css').replace('site-v1.js','site-1.0.0.js')
    s=s.replace('<link rel="icon" href="assets/brand-1.0-normal.png">','<link rel="icon" type="image/x-icon" sizes="any" href="assets/brand-1.0.ico"><link rel="icon" type="image/png" sizes="48x48" href="assets/brand-1.0-normal.png"><link rel="shortcut icon" href="favicon.ico">')
    for r in ['owl','beaver','cat','wolf','rabbit','penguin']:s=s.replace(f'assets/launch-{r}.png',f'assets/crew-1.0-{r}.png')
    s=s.replace('SAMERO-1.9.0.exe','SAMERO-1.0.0-rc1.exe').replace('SAMERO-1.9.0-Portable.zip','SAMERO-1.0.0-rc1-Portable.zip').replace('downloads/SHA256SUMS.txt','downloads/SHA256SUMS-1.0.0-rc1.txt').replace('downloads/TEST-RESULTS.txt','downloads/TEST-RESULTS-1.0.0-rc1.txt')
    s=s.replace('1.9.0-studio-rc1','1.0.0-rc1').replace('1.9.0 RC1','1.0.0 RC1')
    s=s.replace('2ee60d8e59eceaf8e9676bcf53d442cee72c5e01a571158e58d560adb3f0275f',digest(exe))
    s=s.replace('912 KiB',f'{round(exe.stat().st_size/1024)} KiB').replace('566 KiB',f'{round(portable.stat().st_size/1024)} KiB')
    s=s.replace('Ảnh xem trước giao diện bản RC1.','Ảnh chụp ứng dụng 1.0.0 RC1 đang chạy trong môi trường kiểm thử.').replace('Preview of the RC1 interface.','Screenshot of the running 1.0.0 RC1 app in a test environment.')
    s=s.replace('Nhân vật trong ứng dụng RC1; hình minh họa website được làm mới bên dưới.','Bộ nhân vật thống nhất giữa ứng dụng và website.').replace('RC1 in-app characters; refreshed website artwork appears below.','The same character artwork is used in the app and website.')
    s=s.replace('EXE RC1 vẫn dùng sprite gốc.','EXE 1.0.0 RC1 sử dụng chính bộ sprite này.').replace('The RC1 executable retains the original sprites.','The 1.0.0 RC1 executable uses this same sprite set.')
    s=s.replace('Dữ liệu minh họa, không phải tiến độ máy của người xem.','Dữ liệu môi trường kiểm thử, không phải tiến độ máy của người xem.').replace("Illustrative data, not the viewer's current project status.","Test environment data, not the viewer's project status.")
    s=s.replace('assets/SAMERO-Film-1.0.mp4','assets/SAMERO-Film-1.0.0-rc1.mp4').replace('assets/film-poster.jpg','assets/film-poster-1.0.jpg').replace('assets/film-vi.vtt','assets/film-vi-1.0.vtt').replace('assets/film-en.vtt','assets/film-en-1.0.vtt')
    for i in range(3):s=s.replace(f'assets/demo-{i}.jpg',f'assets/demo-1.0-{i}.jpg')
    link='<a download href="downloads/SAMERO-1.0.0-rc1-Source.zip">'+('Tải mã nguồn ZIP' if lang=='vi' else 'Download source ZIP')+'</a>'
    s=s.replace('</div><p id="copy-result"',link+'</div><p id="copy-result"',1)
    assert link in s and '1.9.0' not in s
    (ROOT/filename).write_text(s)
css=(ROOT/'scripts/site-v1.css').read_text()
css+='\n@media(max-width:600px){.mascot{display:flex;justify-content:flex-start;align-items:center;gap:10px}.mascot button{width:72px;height:72px;padding:4px}.mascot img{width:64px;height:64px}.mascot small{text-align:left}.hero-grid{gap:10px}}\n'
(ROOT/'site-1.0.0.css').write_text(css)
js=(ROOT/'scripts/site-v1.js').read_text().replace("assets/open.png","assets/brand-1.0-open.png").replace("assets/normal.png","assets/brand-1.0-normal.png")
(ROOT/'site-1.0.0.js').write_text(js)
# Restore versioned demo images, actual browser crops (not marketing mockups).
for i,f in enumerate(['studio-top.png','office.png','settings.png']):
    src=Image.open(A/f).convert('RGB');canvas=Image.new('RGB',(1200,740),'#0b1828');src=ImageOps.contain(src,(1164,704),Image.Resampling.LANCZOS);canvas.paste(src,((1200-src.width)//2,(740-src.height)//2));canvas.save(A/f'demo-1.0-{i}.jpg',quality=93,optimize=True)
print('PASS: canonical source, portable, EXE, checksum, identical sprites, favicon, versioned page references')
