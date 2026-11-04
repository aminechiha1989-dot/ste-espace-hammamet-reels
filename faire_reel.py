#!/usr/bin/env python3
"""Fabrique un reel vertical 1080x1920 (15 s) pour STE Espace Hammamet.
Usage : python3 faire_reel.py config.json sortie.mp4
config.json = {
  "slides":[ {"photo":"photos/x.jpg","kicker":"NOUVEAUTÉ","title":["Miroir LED","importé"],
              "top_sub":"ligne sous le titre (optionnel)","bottom":["ligne 1","ligne 2"]} , ...],
  "cta":{"lines":["Miroirs LED  •  Cabines de douche","Verre sécurit sur mesure"],"phone":"97 565 783",
         "address":"Av Abu Dhabi, Hammamet"} }
"""
import sys, json, os, subprocess, tempfile, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
W,H,FPS=1080,1920,30
SEG=int(4.5*FPS); FADE=int(0.8*FPS)
def font(bold,size):
    for p in (['/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'] if bold else ['/usr/share/fonts/opentype/inter/Inter-Regular.otf'])+['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        if os.path.exists(p): return ImageFont.truetype(p,size)
    return ImageFont.load_default()
ACC=(226,150,70); WHITE=(255,255,255); SOFT=(240,230,220); INK=(52,42,36); GREY=(110,98,88)
def cover(im):
    w,h=im.size; r=W/H
    if w/h>r: nw=int(h*r); l=(w-nw)//2; im=im.crop((l,0,l+nw,h))
    else: nh=int(w/r); t=(h-nh)//2; im=im.crop((0,t,w,t+nh))
    return im.resize((W,H),Image.LANCZOS)
def shade(im,y0,y1,a0,a1):
    ov=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    for y in range(y0,y1):
        a=int(a0+(a1-a0)*(y-y0)/(y1-y0)); d.line((0,y,W,y),fill=(30,22,16,a))
    return Image.alpha_composite(im.convert('RGBA'),ov).convert('RGB')
def photo_bg(path):
    im=Image.open(path).convert('RGB'); w,h=im.size
    if w/h<0.62: return cover(im)
    bg=cover(im).filter(ImageFilter.GaussianBlur(40))
    fw=W; fh=int(h*W/w); fit=im.resize((fw,fh),Image.LANCZOS)
    bg.paste(fit,(0,(H-fh)//2-60)); return bg
def slide(s,base):
    im=photo_bg(os.path.join(base,s['photo']))
    im=shade(im,0,720,170,0); im=shade(im,1250,1800,0,150)
    d=ImageDraw.Draw(im)
    d.text((70,150),s.get('kicker','STE ESPACE HAMMAMET'),font=font(1,34),fill=ACC)
    d.rectangle((70,200,150,205),fill=ACC)
    y=250
    for line in s['title']:
        d.text((70,y),line,font=font(1,92),fill=WHITE); y+=110
    if s.get('top_sub'): d.text((70,y+20),s['top_sub'],font=font(0,44),fill=SOFT)
    yb=1560
    for i,line in enumerate(s.get('bottom',[])):
        d.text((70,yb),line,font=font(1 if i==0 else 0,50 if i==0 else 44),fill=WHITE if i==0 else SOFT); yb+=70
    return im
def cta(c):
    y=np.linspace(0,1,H)[:,None,None]; c1=np.array([247,240,230]); c2=np.array([226,208,186])
    g=np.broadcast_to((c1*(1-y)+c2*y),(H,W,3)).astype(np.uint8)
    im=Image.fromarray(g); d=ImageDraw.Draw(im)
    d.text((W//2,560),"STE ESPACE",font=font(1,84),fill=INK,anchor='ma')
    d.text((W//2,665),"HAMMAMET",font=font(1,84),fill=ACC,anchor='ma')
    yy=800
    for l in c['lines']: d.text((W//2,yy),l,font=font(0,42),fill=GREY,anchor='ma'); yy+=60
    d.rounded_rectangle((140,1010,940,1150),70,fill=(37,160,90))
    d.text((W//2,1080),"WhatsApp : "+c['phone'],font=font(1,54),fill=WHITE,anchor='mm')
    d.text((W//2,1230),"Demandez votre devis",font=font(0,44),fill=INK,anchor='ma')
    d.text((W//2,1300),c['address'],font=font(0,38),fill=GREY,anchor='ma')
    return im
def zoom(img,k,n):
    z=1.0+0.07*k/n; cw,ch=int(W/z),int(H/z); l=(W-cw)//2; t=(H-ch)//2
    return img.crop((l,t,l+cw,t+ch)).resize((W,H),Image.BILINEAR)
def main(cfg_path,out):
    base=os.path.dirname(os.path.abspath(cfg_path))
    cfg=json.load(open(cfg_path,encoding='utf-8'))
    imgs=[slide(s,base) for s in cfg['slides']]+[cta(cfg['cta'])]
    tmp=tempfile.mkdtemp(); idx=0
    for si,img in enumerate(imgs):
        n=SEG+(FADE if si<len(imgs)-1 else 0)
        for k in range(n):
            f=zoom(img,k,SEG)
            if si>0 and k<FADE: f=Image.blend(zoom(imgs[si-1],SEG+k,SEG),f,k/FADE)
            f.save(os.path.join(tmp,f'f{idx:04d}.jpg'),quality=92); idx+=1
    subprocess.run(['ffmpeg','-y','-v','error','-framerate',str(FPS),'-i',os.path.join(tmp,'f%04d.jpg'),'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',out],check=True)
    shutil.rmtree(tmp); print('OK',out,idx/FPS,'s')
if __name__=='__main__': main(sys.argv[1],sys.argv[2])
