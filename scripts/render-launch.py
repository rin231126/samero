from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import base64, io, hashlib, math, os, subprocess, json, re

ROOT=Path(__file__).resolve().parent.parent
A=ROOT/'assets'
W,H,FPS,DURATION=1920,1080,60,24
ROLES=['owl','beaver','cat','wolf','rabbit','penguin']
NAMES=['Manager','Researcher','Architect','Developer','Reviewer','Tester','Auditor']
SUBS=['Coordinate','Research','Plan','Build','Review','Test','Audit']
FONTS={}
def font(size,bold=False):
    key=(size,bold)
    if key not in FONTS:
        FONTS[key]=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',size)
    return FONTS[key]
def ease(x):
    x=max(0,min(1,x));return x*x*(3-2*x)
def label(d,xy,s,size=28,color='#9ab5d0',bold=False,anchor=None):
    d.text(xy,s,font=font(size,bold),fill=color,anchor=anchor)
def rounded(d,box,fill='#11263b',outline='#2c4c65',radius=24,width=2):
    d.rounded_rectangle(box,radius,fill=fill,outline=outline,width=width)
def sprite(im,xy,asset,size):
    s=asset.resize((size,size),Image.Resampling.NEAREST);im.paste(s,tuple(map(int,xy)),s)
# Source artwork is a six-cell, transparent pixel-art sheet.
raw=base64.b64decode((ROOT/'scripts/launch-team.b64').read_text().strip(),validate=True)
assert hashlib.sha256(raw).hexdigest()=='609d60f485b25062d39716949ed6ae5827a8d4cda20ff3e12e694981e6f57551'
sheet=Image.open(io.BytesIO(raw)).convert('RGBA')
assert sheet.size==(288,48)
for i,r in enumerate(ROLES):
    im=sheet.crop((i*48,0,(i+1)*48,48))
    assert im.getchannel('A').getextrema()==(0,255)
    im.save(A/f'launch-{r}.png',optimize=True)
team=[Image.open(A/'normal.png').convert('RGBA')]+[Image.open(A/f'launch-{r}.png').convert('RGBA') for r in ROLES]
ui=Image.open(A/'studio-top.png').convert('RGB')
bg=Image.new('RGB',(W,H));d=ImageDraw.Draw(bg)
for y in range(H):
    t=y/H;d.line((0,y,W,y),fill=(int(10+5*t),int(22+8*t),int(38+14*t)))
for x in range(80,W,80):d.line((x,0,x,H),fill='#14283d')
for y in range(80,H,80):d.line((0,y,W,y),fill='#14283d')
def base(k):
    im=bg.copy();d=ImageDraw.Draw(im)
    d.line((104,94,W-104,94),fill='#29445d',width=2)
    label(d,(104,52),'SAMERO / PIXEL AI STUDIO',24,'#8bd7ff',True)
    label(d,(W-104,52),'FIRST RELEASE   /   01',24,'#9ab5d0',anchor='ra')
    label(d,(104,H-70),'INDEPENDENT DESKTOP TOOL  |  WINDOWS x64',22,'#9ab5d0')
    label(d,(W-104,H-70),f'0{k+1} / 04',24,'#8bd7ff',anchor='ra')
    return im
plates=[base(i) for i in range(4)]
im=plates[0];d=ImageDraw.Draw(im)
label(d,(960,226),'YOUR CREATIVE WORKSPACE',32,'#8bd7ff',True,'mm')
label(d,(960,354),'SAMERO',154,'#f2f8ff',True,'mm')
label(d,(960,467),'Build. Develop. Your own way.',49,'#c4def5',False,'mm')
rounded(d,(715,820,1205,885),'#143451','#3979aa',32)
label(d,(960,852),'PIXEL AI STUDIO / RC1',27,'#b9e9ff',True,'mm')
im=plates[1];d=ImageDraw.Draw(im)
label(d,(104,161),'01 / THE WORKSPACE',25,'#8bd7ff',True)
label(d,(104,231),'One place.',77,'#f2f8ff',True)
label(d,(104,325),'More clarity.',77,'#f2f8ff',True)
for i,(a,b) in enumerate([('PROJECTS','Organize your work'),('CHECKPOINTS','Track verified progress'),('CODEX','Manage development sessions')]):
    y=486+i*125;rounded(d,(104,y,645,y+105),'#142b41','#2d4c65',18)
    label(d,(130,y+15),a,22,'#8bd7ff',True);label(d,(130,y+53),b,25,'#e2edf8')
label(d,(1240,934),'Actual interface preview  |  v1.9.0 RC1',22,'#9ab5d0',False,'mm')
im=plates[2];d=ImageDraw.Draw(im)
label(d,(960,180),'02 / MEET THE CREW',25,'#8bd7ff',True,'mm')
label(d,(960,268),'Seven roles. One studio.',78,'#f2f8ff',True,'mm')
label(d,(960,348),'A pixel personality for every workflow.',34,'#adc9df',False,'mm')
label(d,(960,913),'Illustrated role mascots  |  Not independent running agents',25,'#a1bdd4',False,'mm')
im=plates[3];d=ImageDraw.Draw(im)
label(d,(960,270),'03 / READY TO EXPLORE',26,'#8bd7ff',True,'mm')
label(d,(960,385),'Make it yours.',98,'#f2f8ff',True,'mm')
label(d,(960,494),'Six themes. Local workflow. Pixel character.',36,'#b9d4eb',False,'mm')
rounded(d,(590,660,1330,766),'#a7e3ff','#d1f3ff',52)
label(d,(960,713),'DOWNLOAD FOR WINDOWS',32,'#08233a',True,'mm')
label(d,(960,841),'v1.9.0-studio-rc1  |  EXE / Portable ZIP',28,'#b3cde3',False,'mm')
label(d,(960,894),'Unsigned release candidate - full Windows testing pending',23,'#8daac1',False,'mm')
panel=Image.new('RGB',(1148,735),'#091724');pd=ImageDraw.Draw(panel)
rounded(pd,(1,1,1146,733),'#0b1928','#416a8d',24,3)
for i,c in enumerate(['#ef9b9b','#f1cb83','#91dcb8']):pd.ellipse((30+i*30,22,47+i*30,39),fill=c)
label(pd,(574,30),'SAMERO / PIXEL STUDIO',18,'#9ab5d0',True,'mm')
screen=ImageOps.contain(ui,(1116,674),Image.Resampling.LANCZOS);panel.paste(screen,((1148-screen.width)//2,54))
def frame(k,t):
    im=plates[k].copy();d=ImageDraw.Draw(im);p=ease(t/1.1)
    if k==0:
        sprite(im,(832,535+int(8*math.sin(t*2))),team[0],256)
    elif k==1:
        x=676+int((1-p)*65);im.paste(panel,(x,164))
    elif k==2:
        for j,asset in enumerate(team):
            q=ease((t-j*.11)/.9);x=108+j*246;y=424+int((1-q)*60)
            rounded(d,(x,y,x+226,y+365),'#12283e','#345872',22,2)
            d.ellipse((x+48,y+37,x+178,y+167),fill='#193b59')
            sprite(im,(x+17,y+24+int(5*math.sin(t*2+j*.7))),asset,192)
            label(d,(x+113,y+257),NAMES[j],24,'#f0f7ff',True,'mm')
            label(d,(x+113,y+302),SUBS[j],22,'#a3c3db',False,'mm')
    elif k==3:
        for j,c in enumerate(['#3f97e7','#a37ee9','#f2a9cf','#6ed7a0','#d9eaff','#779bd0']):
            x=694+j*90;rounded(d,(x,552,x+80,582),c,c,12)
    d.rectangle((104,H-22,W-104,H-17),fill='#25435c');d.rectangle((104,H-22,104+int((W-208)*(k*6+t)/DURATION),H-17),fill='#8bd7ff')
    return im
out=A/'SAMERO-Launch-Trailer.mp4'
cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(FPS),'-i','pipe:0','-i',str(A/'SAMERO-Intro.mp4'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-threads','4','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-af','afade=t=in:st=0:d=0.6,afade=t=out:st=22.5:d=1.5','-t',str(DURATION),'-movflags','+faststart',str(out)]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
try:
    for n in range(DURATION*FPS):
        t=n/FPS;k=min(3,int(t//6));local=t-k*6;im=frame(k,local)
        if k and local<.55:im=Image.blend(frame(k-1,6),im,ease(local/.55))
        if t<.35:im=Image.blend(bg,im,ease(t/.35))
        if t>23.6:im=Image.blend(im,bg,ease((t-23.6)/.4))
        proc.stdin.write(im.tobytes())
finally:
    proc.stdin.close()
assert proc.wait()==0
frame(2,2).save(A/'launch-poster.jpg',quality=92,optimize=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out)]))
video=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==(1920,1080,'60/1','1440')
assert any(s['codec_type']=='audio' for s in probe['streams'])
assert abs(float(probe['format']['duration'])-24)<.1
# Decode the entire MP4 once; reject broken streams before publishing.
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(out),'-f','null','-'],check=True)
vtt='WEBVTT\n\n00:00:00.350 --> 00:00:05.900\nSAMERO — Không gian làm việc sáng tạo của bạn.\n\n00:00:06.000 --> 00:00:11.900\nQuản lý dự án, mốc kiểm chứng và các phiên Codex.\n\n00:00:12.000 --> 00:00:17.900\nBảy vai trò, một studio. Hình minh họa nhân vật, không phải AI chạy độc lập.\n\n00:00:18.000 --> 00:00:23.500\nSáu giao diện. Tải bản thử nghiệm Windows x64. Chưa ký số.\n'
(A/'launch-vi.vtt').write_text(vtt,encoding='utf-8')
css='''\n/* Launch artwork: keep original logo; better contrast and role hierarchy. */
.team-grid>div{border:1px solid var(--line);padding:15px 4px 13px;position:relative;background:radial-gradient(ellipse at 50% 18%,var(--glow),transparent 70%),var(--surface);transition:transform .24s ease,border-color .24s ease}
.team-grid img{width:88px;height:88px;image-rendering:pixelated;object-fit:contain;transition:transform .24s ease}
.team-grid>div:hover{transform:translateY(-4px);border-color:var(--accent)}
.team-grid>div:hover img{transform:translateY(-3px)}
.team-grid b{margin-top:5px;font-size:12px}
.team-grid small{margin-top:4px}
@media(max-width:540px){.team-grid img{width:64px;height:64px}.team-grid>div{padding:12px 2px}}
@media(prefers-reduced-motion:reduce){.team-grid>div,.team-grid img{transition:none!important;transform:none!important}}
'''
for page in ('index.html','en.html'):
    p=ROOT/page;s=p.read_text(encoding='utf-8')
    assert 'assets/SAMERO-Intro.mp4' in s and 'assets/trailer-poster.jpg' in s
    for r in ROLES:
        old=f'assets/office-{r}.png';assert old in s
        s=s.replace(old,f'assets/launch-{r}.png')
    s=s.replace('assets/SAMERO-Intro.mp4','assets/SAMERO-Launch-Trailer.mp4').replace('assets/trailer-poster.jpg','assets/launch-poster.jpg')
    s=s.replace('height="720" playsinline=""','height="1080" playsinline=""').replace('preload="metadata" width="1280"','preload="metadata" width="1920"')
    if page=='index.html':
        s=s.replace('36 giây · tiếng Việt','24 giây · 1080p60 · phụ đề Việt')
        s=s.replace('Các nhân vật đại diện cho vai trò trong prompt, không mô phỏng tiến trình AI đang chạy.','Hình minh họa mới dành cho website; bản EXE RC1 vẫn dùng sprite cũ. Các nhân vật đại diện cho vai trò trong prompt, không mô phỏng AI đang chạy.')
        s=s.replace('type="video/mp4"/>','type="video/mp4"/><track kind="subtitles" srclang="vi" label="Tiếng Việt" src="assets/launch-vi.vtt" default="">',1)
    else:
        s=s.replace('36 seconds · Vietnamese','24 seconds · 1080p60 · English text')
        s=s.replace('Characters represent prompt roles, not simulated live AI activity.','New promotional artwork for the website; the RC1 executable retains its original sprites. Characters represent prompt roles, not simulated live AI activity.')
        s=s.replace('type="video/mp4"/>','type="video/mp4"/><track kind="subtitles" srclang="vi" label="Tiếng Việt" src="assets/launch-vi.vtt">',1)
    s=s.replace('</style>',css+'</style>',1)
    for ref in re.findall(r'(?:src|href|poster)="([^"]+)"',s):
        if ref.startswith(('assets/','downloads/')):assert (ROOT/ref).is_file(),ref
    p.write_text(s,encoding='utf-8')
print('PASS: 6 sprites, 1920x1080, 60 fps, 1440 frames, 24 seconds, audio, full decode, local references')
