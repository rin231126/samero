from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import math, subprocess, json, hashlib

ROOT=Path(__file__).resolve().parent.parent
A=ROOT/'assets'
W,H,FPS,SECONDS=1920,1080,60,30
FONTS={}
def font(n,bold=False):
    key=(n,bold)
    if key not in FONTS:
        FONTS[key]=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',n)
    return FONTS[key]
def ease(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
def text(d,xy,s,n=26,c='#b2c8de',bold=False,anchor=None):
    d.text(xy,s,font=font(n,bold),fill=c,anchor=anchor)
def box(d,b,fill='#10253b',stroke='#315570',radius=24):
    d.rounded_rectangle(b,radius,fill=fill,outline=stroke,width=2)
def paste_sprite(im,asset,x,y,size):
    s=asset.resize((size,size),Image.Resampling.NEAREST)
    im.paste(s,(int(x),int(y)),s)
def draw_image(im,asset,bounds):
    x,y,w,h=bounds
    s=ImageOps.contain(asset,(w,h),Image.Resampling.LANCZOS)
    im.paste(s,(x+(w-s.width)//2,y+(h-s.height)//2))
roles=['Manager','Researcher','Architect','Developer','Reviewer','Tester','Auditor']
subs=['Coordinate','Research','Plan','Develop','Review','Test','Audit']
sprites=[Image.open(A/'normal.png').convert('RGBA')]+[Image.open(A/f'launch-{x}.png').convert('RGBA') for x in ['owl','beaver','cat','wolf','rabbit','penguin']]
ui=Image.open(A/'studio-top.png').convert('RGB')
assert ui.size==(1500,925)
# These are crops of the authentic static interface preview, never simulated test results.
for i,b in enumerate([(0,0,1500,925),(165,220,1500,625),(165,630,1500,925)]):
    canvas=Image.new('RGB',(1200,740),'#0b1828')
    draw_image(canvas,ui.crop(b),(18,18,1164,704))
    canvas.save(A/f'demo-{i}.jpg',quality=92,optimize=True)
bg=Image.new('RGB',(W,H)); pix=bg.load()
for y in range(H):
    for x in range(W):
        v=max(0,1-math.hypot((x-1200)/1400,(y-370)/1000))
        pix[x,y]=(int(8+v*11),int(15+v*24),int(29+v*38))
d=ImageDraw.Draw(bg)
for x in range(0,W,96):
    for y in range(0,H,96):d.ellipse((x+20,y+20,x+22,y+22),fill='#244460')
def plate(k):
    im=bg.copy();d=ImageDraw.Draw(im)
    d.line((100,92,1820,92),fill='#294863',width=2)
    text(d,(100,48),'SAMERO  /  OCEAN LAB',25,'#a7e3ff',True)
    text(d,(1820,48),'LAUNCH FILM  /  01',22,'#b2c8de',anchor='ra')
    text(d,(100,1023),'INDEPENDENT AI-ASSISTED DEVELOPMENT WORKSPACE',20,'#96b1c8')
    text(d,(1820,1023),f'0{k+1} / 05',22,'#a7e3ff',True,'ra')
    return im
plates=[plate(i) for i in range(5)]
bounds=[0,5,12,18,24,30]
# Window with the authentic RC1 preview.
window=Image.new('RGB',(1320,850),'#0b1726')
d=ImageDraw.Draw(window);box(d,(1,1,1318,848),'#0c1a2b','#567d9f',20)
for j,c in enumerate(['#ef939d','#e8c282','#8ae0c0']):d.ellipse((26+29*j,19,43+29*j,36),fill=c)
text(d,(660,29),'SAMERO / ACTUAL SAMERO 1.0.0 RC1',18,'#b5cbde',True,'mm')
draw_image(window,ui,(14,52,1292,783))
# Pre-render the crop for smooth camera motion with no synthetic clicks.
detail=ui.crop((165,630,1500,925)).resize((1335,295),Image.Resampling.LANCZOS)
purple=Image.open(A/'studio-purple.png').convert('RGB')
assert purple.size==(1500,925)
purple_window=window.copy();draw_image(purple_window,purple,(14,52,1292,783))
def frame(k,t):
    im=plates[k].copy();d=ImageDraw.Draw(im)
    p=ease(t/.95)
    if k==0:
        x=100+int(46*(1-p))
        text(d,(x,225),'A CREATIVE WORKSPACE',30,'#a7e3ff',True)
        text(d,(x,295),'Build.',120,'#f0f7ff',True)
        text(d,(x,425),'Develop.',120,'#f0f7ff',True)
        text(d,(x,565),'Your own way.',91,'#a7e3ff',True)
        text(d,(x,710),'AI-assisted project development.',35,'#b2c8de')
        # Original logo with nearest-neighbor rendering.
        d.ellipse((1120,234,1740,854),fill='#122b48',outline='#355b81',width=3)
        paste_sprite(im,sprites[0],1240,310+int(14*math.sin(t*2)),384)
        text(d,(1430,800),'PIXEL AI STUDIO',27,'#a7e3ff',True,'mm')
    elif k==1:
        text(d,(100,188),'01 / PRODUCT',25,'#a7e3ff',True)
        text(d,(100,243),'Your',74,'#f0f7ff',True)
        text(d,(100,330),'workspace.',69,'#f0f7ff',True)
        text(d,(100,448),'Projects',32,'#b2c8de',True)
        text(d,(100,500),'Codex sessions',32,'#b2c8de')
        text(d,(100,552),'Pixel Studio',32,'#b2c8de')
        text(d,(100,626),'Actual interface preview',22,'#a7e3ff')
        text(d,(100,661),'Test environment / RC1',21,'#96b1c8')
        x=566+int(60*(1-p))
        im.paste(Image.blend(window,purple_window,ease((t-3.7)/.8)*(1-ease((t-5.6)/.8))),(x,120))
    elif k==2:
        text(d,(960,178),'02 / WORKFLOW',25,'#a7e3ff',True,'mm')
        text(d,(960,260),'Keep the progress.',82,'#f0f7ff',True,'mm')
        text(d,(960,342),'A project, a plan, and evidence.',34,'#b2c8de',False,'mm')
        steps=[('01','Plan','Organize the work'),('02','Develop','Use Codex sessions'),('03','Verify','Record checkpoints')]
        for j,(n,h,sub) in enumerate(steps):
            q=ease((t-j*.36)/.7);x=100+590*j;y=414+int(55*(1-q))
            box(d,(x,y,x+540,y+215),'#10253b','#467293',23)
            text(d,(x+30,y+30),n,24,'#a7e3ff',True)
            text(d,(x+30,y+82),h,50,'#f0f7ff',True)
            text(d,(x+30,y+150),sub,25,'#b2c8de')
        # A real crop of the existing preview, explicitly labeled.
        im.paste(detail,(292,670))
        text(d,(960,978),'Checkpoint view / test environment',20,'#a7e3ff',False,'mm')
    elif k==3:
        text(d,(960,180),'03 / PIXEL OCEAN',25,'#a7e3ff',True,'mm')
        text(d,(960,268),'Meet the crew.',88,'#f0f7ff',True,'mm')
        text(d,(960,348),'Seven prompt roles, one creative identity.',34,'#b2c8de',False,'mm')
        for j,s in enumerate(sprites):
            q=ease((t-j*.12)/.8);x=102+j*246;y=438+int((1-q)*55)
            box(d,(x,y,x+230,y+365),'#11263c','#365c7b',24)
            d.ellipse((x+42,y+37,x+188,y+183),fill='#1c3c59')
            paste_sprite(im,s,x+19,y+23+int(5*math.sin(t*2+j*.65)),192)
            text(d,(x+115,y+260),roles[j],24,'#f0f7ff',True,'mm')
            text(d,(x+115,y+302),subs[j],22,'#b2c8de',False,'mm')
        text(d,(960,907),'Same artwork in the app and website / illustrated roles',23,'#a7e3ff',False,'mm')
    else:
        text(d,(960,220),'04 / FIRST LOOK',25,'#a7e3ff',True,'mm')
        text(d,(960,330),'Make it yours.',105,'#f0f7ff',True,'mm')
        text(d,(960,460),'Six themes. Local workflow. Pixel identity.',36,'#b2c8de',False,'mm')
        for j,c in enumerate(['#4da4e9','#ae91eb','#f2b3d9','#7cdfa6','#d9eaff','#7289a5']):
            x=684+j*93;box(d,(x,555,x+82,590),c,c,11)
        y=682+int(24*(1-p));box(d,(566,y,1354,y+103),'#a7e3ff','#d4f3ff',49)
        text(d,(960,y+51),'DOWNLOAD FOR WINDOWS',34,'#0a233a',True,'mm')
        text(d,(960,854),'SAMERO 1.0.0 RC1  /  Windows x64',28,'#b2c8de',False,'mm')
        text(d,(960,902),'Unsigned release candidate. Full Windows verification pending.',22,'#a7e3ff',False,'mm')
    d.rectangle((100,H-19,1820,H-14),fill='#233f58')
    d.rectangle((100,H-19,100+int(1720*(bounds[k]+t)/SECONDS),H-14),fill='#a7e3ff')
    return im
out=A/'SAMERO-Film-1.0.0-rc1.mp4'
cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(A/'SAMERO-Intro.mp4'),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-threads','4','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-af','afade=t=in:st=0:d=0.6,afade=t=out:st=28:d=2','-t',str(SECONDS),'-movflags','+faststart',str(out)]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
try:
    for n in range(SECONDS*FPS):
        t=n/FPS;k=next(j for j in range(5) if t<bounds[j+1]);local=t-bounds[k]
        im=frame(k,local)
        if k and local<.65:im=Image.blend(frame(k-1,bounds[k]-bounds[k-1]),im,ease(local/.65))
        if t<.3:im=Image.blend(bg,im,ease(t/.3))
        if t>29.5:im=Image.blend(im,bg,ease((t-29.5)/.5))
        proc.stdin.write(im.tobytes())
finally:proc.stdin.close()
assert proc.wait()==0
frame(0,1.2).save(A/'film-poster-1.0.jpg',quality=92,optimize=True)
# Contact sheet records representative frames for visual QA.
contact=Image.new('RGB',(960,270*5),'#080f1c')
for i in range(5):contact.paste(frame(i,2).resize((960,540),Image.Resampling.LANCZOS).resize((480,270)),(0,i*270))
for i in range(5):contact.paste(frame(i,4).resize((480,270),Image.Resampling.LANCZOS),(480,i*270))
contact.save(ROOT/'film-contact-sheet.jpg',quality=90)
captions={
'vi':['SAMERO — Không gian phát triển sáng tạo.','Tổng quan giao diện Pixel Studio và quản lý dự án.','Lập kế hoạch, phát triển với Codex, ghi nhận checkpoint.','Bảy vai trò minh họa; không phải agent chạy độc lập.','SAMERO 1.0.0 RC1. Tải bản Windows x64 chưa ký số.'],
'en':['SAMERO — A creative development workspace.','Pixel Studio and project organization.','Plan, develop with Codex, and preserve checkpoints.','Seven illustrated prompt roles, not independent active agents.','SAMERO 1.0.0 RC1. Unsigned Windows x64 release candidate.']}
for lang,lines in captions.items():
    v='WEBVTT\n\n'
    for i,line in enumerate(lines):
        v+=f'00:00:{bounds[i]:02d}.000 --> 00:00:{bounds[i+1]:02d}.000\n{line}\n\n'
    (A/f'film-{lang}-1.0.vtt').write_text(v,encoding='utf-8')
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out)]))
video=next(s for s in probe['streams'] if s['codec_type']=='video')
assert (video['width'],video['height'],video['r_frame_rate'],video['nb_frames'])==(W,H,'60/1','1800')
assert any(s['codec_type']=='audio' for s in probe['streams'])
assert abs(float(probe['format']['duration'])-SECONDS)<.1
subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(out),'-f','null','-'],check=True)
print('PASS: 30 seconds, 1920x1080, 60 fps, 1800 frames, audio, full decode, both subtitle files')
