#!/usr/bin/env python3
"""Generate original editorial story artwork without external image licensing."""
import hashlib
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PALETTES=[("#121e2c","#19b9b0"),("#201b32","#d995fc"),("#16283b","#f8b55b"),("#1d2830","#b1db63"),("#282032","#fa817e")]

def render(headline,source,index,path):
    w,h=1280,720
    bg,accent=PALETTES[(index-1)%len(PALETTES)]
    im=Image.new("RGB",(w,h),bg)
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,16,h),fill=accent)
    d.rectangle((65,68,210,74),fill=accent)
    d.text((65,90),"PERSONAL NEWS HOST",font=ImageFont.truetype(BOLD,23),fill="#f0f5fa")
    d.text((65,151),f"NACHRICHT  {index:02d} / 05",font=ImageFont.truetype(FONT,27),fill=accent)
    # Abstract broadcast shapes, not third-party photographs.
    for j in range(5):
        x=885+j*85
        d.ellipse((x-80,180+j*27,x+250,510+j*27),outline=accent,width=3)
    d.rounded_rectangle((58,218,1190,576),radius=18,fill="#0b1322")
    d.rectangle((58,218,70,576),fill=accent)
    font_size=53
    while font_size>=28:
        font=ImageFont.truetype(BOLD,font_size)
        lines=[]
        words=headline.split()
        line=""
        for word in words:
            trial=(line+" "+word).strip()
            if d.textbbox((0,0),trial,font=font)[2]>1020 and line:
                lines.append(line);line=word
            else:line=trial
        if line:lines.append(line)
        if len(lines)*int(font_size*1.34)<=280:break
        font_size-=3
    y=270
    for line in lines[:7]:
        d.text((100,y),line,font=font,fill="#f4f7fc")
        y+=int(font_size*1.34)
    d.rectangle((65,637,1220,640),fill="#536577")
    d.rectangle((65,637,65+int(1155*index/5),640),fill=accent)
    d.text((65,663),f"QUELLE: {source[:70] or 'RSS'}",font=ImageFont.truetype(FONT,20),fill="#d8e3ec")
    d.text((1110,663),"PNH",font=ImageFont.truetype(BOLD,22),fill=accent)
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    im.save(path)
