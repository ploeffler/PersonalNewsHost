"""Calibrated 2D lip deformation; colour search is a heuristic, not face recognition."""
import array
import math
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


def mouth_box(image, mouth):
    values = [float(mouth[k]) for k in ('x', 'y', 'width', 'height')]
    x, y, width, height = values
    if not all(math.isfinite(v) for v in values) or not (0 < width < .5 and 0 < height < .3 and width/2 < x < 1-width/2 and height/2 < y < 1-height/2):
        raise ValueError('Mouth rectangle must fit inside the image')
    w, h = image.size
    return (round((x-width/2)*w), round((y-height/2)*h), round((x+width/2)*w), round((y+height/2)*h))


def locate_lips(image, region):
    """Find a compact lipstick component inside an explicitly selected mouth ROI.

    Never search the full scene: another face, wallpaper or clothing can be red.
    Weak/ambiguous results require manual calibration rather than a guessed face.
    """
    left, top, right, bottom = mouth_box(image, region)
    pixels = image.convert('RGB').load(); candidates = set()
    for y in range(top, bottom):
        for x in range(left, right):
            r, g, b = pixels[x, y]
            if r > 65 and r-g > 35 and b-g > 12 and r > b*.85:
                candidates.add((x, y))
    components = []
    while candidates:
        start = candidates.pop(); stack = [start]; points = [start]
        while stack:
            x, y = stack.pop()
            for point in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if point in candidates:
                    candidates.remove(point); stack.append(point); points.append(point)
        xs, ys = zip(*points); bw = max(xs)-min(xs)+1; bh = max(ys)-min(ys)+1
        if len(points) >= 12 and 1.25 <= bw/bh <= 6 and bw >= (right-left)*.12:
            components.append((len(points), min(xs), min(ys), max(xs)+1, max(ys)+1))
    components.sort(reverse=True)
    if not components or (len(components)>1 and components[1][0] > components[0][0]*.7):
        raise ValueError('Lips uncertain: tighten the mouth search region or supply manual calibration')
    _, x0, y0, x1, y1 = components[0]; w,h=image.size
    lip_pixels=[(x,y) for y in range(y0,y1) for x in range(x0,x1)
                if (lambda rgb: rgb[0]>65 and rgb[0]-rgb[1]>35 and rgb[2]-rgb[1]>12 and rgb[0]>rgb[2]*.85)(pixels[x,y])]
    mean_x=sum(x for x,y in lip_pixels)/len(lip_pixels);mean_y=sum(y for x,y in lip_pixels)/len(lip_pixels)
    slope=sum((x-mean_x)*(y-mean_y) for x,y in lip_pixels)/max(1,sum((x-mean_x)**2 for x,y in lip_pixels))
    return {'x':(x0+x1)/2/w, 'y':(y0+y1)/2/h,
            'width':(x1-x0)*1.15/w, 'height':(y1-y0)*1.25/h,
            'slope':max(-.5,min(.5,slope)), 'method':'lipstick_component_in_selected_roi'}


def calibration(image, mouth):
    result = image.convert('RGB').copy(); d=ImageDraw.Draw(result)
    box=mouth_box(image,mouth); d.rectangle(box, outline='#00ff80', width=2)
    return result


def animate(image, mouth, opening):
    """Warp existing lips/jaw with a feathered boundary; retain original at rest."""
    opening = max(0., min(1., opening))
    frame = image.convert('RGBA').copy()
    if opening < .025:
        return frame
    x0,y0,x1,y1 = mouth_box(frame,mouth); mw=x1-x0; mh=y1-y0
    cx=(x0+x1)/2; seam=y0+mh*.46; gap=opening*mh*.42
    slope=float(mouth.get('slope',0))
    if not math.isfinite(slope) or abs(slope)>.5:
        raise ValueError('Invalid lip slope')
    box=(max(0,x0-mw//2),max(0,y0-mh),min(frame.width,x1+mw//2),min(frame.height,y1+mh*2))
    source=frame.crop(box); patch=source.copy(); src=source.load(); dst=patch.load()
    # Pull lower lip/chin down rather than stretching a rectangle over both lips.
    for y in range(patch.height):
        gy=y+box[1]
        for x in range(patch.width):
            gx=x+box[0]; horizontal=max(0.,1-((gx-cx)/(mw*.85))**2)
            local_seam=seam+(gx-cx)*slope
            vertical=max(0.,min(1.,(gy-local_seam+mh*.2)/(mh*.65))) * max(0.,1-(gy-local_seam)/(mh*3))
            sy=max(0.,min(source.height-1.,y-gap*horizontal*vertical)); low=int(sy); high=min(source.height-1,low+1); frac=sy-low
            dst[x,y]=tuple(round(a*(1-frac)+b*frac) for a,b in zip(src[x,low],src[x,high]))
    d=ImageDraw.Draw(patch)
    # Opening follows the selected lip width and retains both outer lip contours.
    points=[]
    for step in range(40):
        theta=step*math.tau/40;dx=math.cos(theta)*mw*.34
        points.append((cx+dx-box[0],seam+dx*slope+gap/2+math.sin(theta)*gap/2-box[1]))
    d.polygon(points,fill='#301323')
    mask=Image.new('L',patch.size,0);ImageDraw.Draw(mask).ellipse((2,2,patch.width-3,patch.height-3),fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(max(1,mh*.25)))
    frame.paste(patch,box[:2],mask)
    return frame


def speech_envelope(wav_path, fps):
    if not 5 <= fps <= 30:
        raise ValueError('Use 5 to 30 fps')
    with wave.open(str(wav_path),'rb') as audio:
        if audio.getsampwidth()!=2 or audio.getnchannels()!=1:
            raise ValueError('Use mono PCM16 WAV')
        rate=audio.getframerate(); samples=array.array('h',audio.readframes(audio.getnframes()))
    if not samples:
        raise ValueError('Empty speech')
    energy=[]
    for i in range(math.ceil(len(samples)/rate*fps)):
        center=int((i+.5)*rate/fps); values=samples[max(0,center-rate//80):min(len(samples),center+rate//80)]
        energy.append(math.sqrt(sum(v*v for v in values)/max(1,len(values)))/32768)
    peak=max(.015,sorted(energy)[int((len(energy)-1)*.9)]); previous=0.; output=[]
    for rms in energy:
        target=max(0.,min(1.,(rms/peak-.10)/.9)) if rms>.004 else 0.
        # Fast attack, slightly slower release; silence closes the lips exactly.
        previous=0. if rms<=.004 else previous+(target-previous)*(.85 if target>previous else .65)
        output.append(previous)
    return output


def generate_frames(portrait, wav_path, output_dir, fps=20, mouth=None):
    image=Image.open(portrait).convert('RGBA');image.thumbnail((530,665),Image.Resampling.LANCZOS)
    mouth=mouth or {'x':.5,'y':.34,'width':.13,'height':.09}
    mouth_box(image,mouth)
    output=Path(output_dir); output.mkdir(parents=True,exist_ok=True)
    envelope=speech_envelope(wav_path,fps)
    for i,opening in enumerate(envelope):
        animate(image,mouth,opening).save(output/f'lip_{i:06d}.png',compress_level=1)
    return len(envelope)
