#!/usr/bin/env python3
"""RSS preview -> local speech -> continuously animated 2D host -> one MP4.

No model/API payments or publisher. The local animation is an amplitude-driven
2D approximation with body motion, not neural/phoneme-accurate avatar synthesis.
"""
import argparse
import ctypes
import ctypes.util
from datetime import datetime
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import wave
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlsplit
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont, ImageOps

try:
    from .collect_news import parse_feed, clean
    from .editorial_pipeline import sentence_units
    from .promo_lips import generate_frames, locate_lips, calibration
    from .promo_voice import synthesize, PRODUCTION_VOICE
    from .promo_network import fetch_public, validate_feed_url, MAX_FEED_BYTES
except ImportError:
    from collect_news import parse_feed, clean
    from editorial_pipeline import sentence_units
    from promo_lips import generate_frames, locate_lips, calibration
    from promo_voice import synthesize, PRODUCTION_VOICE
    from promo_network import fetch_public, validate_feed_url, MAX_FEED_BYTES

ROOT = Path(__file__).resolve().parents[1]
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
STYLES = {'studio': '#193044', 'technik': '#102d48', 'neutral': '#28343b'}

RENDER_MODES = {
    '2d-local': {'label': '2D lokal', 'dimension': '2d', 'location': 'local', 'status': 'ready',
                 'requirements': ['Pillow', 'FFmpeg', 'eSpeak-NG'], 'cost_preview': 'Keine externe Renderabrechnung; lokale Rechenkosten.'},
    '3d-local': {'label': '3D lokal', 'dimension': '3d', 'location': 'local', 'status': 'setup_required',
                 'requirements': ['Blender-Adapter', 'geriggter Avatar', 'Gesichtssteuerung und Studio'],
                 'cost_preview': 'Noch nicht berechenbar; lokale Renderdauer/GPU-Konfiguration fehlt.'},
    '3d-online': {'label': '3D online', 'dimension': '3d', 'location': 'online', 'status': 'setup_required',
                  'requirements': ['Renderdienst-Adapter', 'Zugangsdaten', 'kompatibler Avatar und Studio'],
                  'cost_preview': None, 'requires_approval': True,
                  'data_to_transfer': ['freigegebene Kurztexte/Sprachspur', 'Avatar- und Studiomedien', 'Renderparameter']},
}


class RenderNotConfigured(ValueError):
    pass


def fit_card(text, width=450, height=390):
    """Fit the entire approved card into its pixel box; never silently crop it."""
    draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))
    for size in range(23, 13, -1):
        font = ImageFont.truetype(FONT, size)
        lines = []
        for paragraph in text.split('\n'):
            line = ''
            # Character wrapping also handles long URLs/names without spaces.
            for char in paragraph:
                candidate = line + char
                if font.getlength(candidate) > width and line:
                    split = line.rfind(' ')
                    if split > 0:
                        lines.append(line[:split]); line = line[split+1:] + char
                    else:
                        lines.append(line); line = char
                else:
                    line = candidate
            lines.append(line)
        wrapped = '\n'.join(lines)
        box = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=6)
        if box[2] <= width and box[3] <= height:
            return font, wrapped
    raise ValueError('Text card does not fit the visible area')


def bounded(value, limit=120):
    if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(c) < 32 for c in value):
        raise ValueError('Missing, oversized or invalid text')
    return value.strip()


class Site(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []; self.parts = []; self.skip = 0
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {'script', 'style'}: self.skip += 1
        if tag == 'a' and attrs.get('href'): self.links.append(attrs['href'])
    def handle_endtag(self, tag):
        if tag in {'script', 'style'}: self.skip = max(0, self.skip - 1)
    def handle_data(self, data):
        if not self.skip: self.parts.append(data.strip())


def operator_research(feed_url, homepage, feed_title, fetch):
    result = {'feed_title': feed_title, 'domain': urlsplit(feed_url).hostname,
              'status': 'unverified', 'operator': None, 'evidence': []}
    if not homepage: return result
    visited = set(); queue = [homepage]
    while queue and len(visited) < 3:
        url = queue.pop(0)
        if url in visited: continue
        visited.add(url)
        try:
            validate_feed_url(url, resolve=False)
            document = Site(); document.feed(fetch(url).decode('utf-8', errors='replace'))
            text = re.sub(r'\s+', ' ', ' '.join(document.parts))
            match = re.search(r'(?:Medieninhaber|Herausgeber|Betreiber|Anbieter)\s*:?\s+([^.!?]{3,120})', text, re.I)
            result['evidence'].append({'url': url, 'kind': 'publisher_statement' if match else 'website',
                                       'excerpt': match.group(0)[:180] if match else None})
            if match:
                result.update(status='self_declared', operator=match.group(1).strip())
                break
            for href in document.links:
                target = urljoin(url, href)
                if urlsplit(target).hostname == urlsplit(homepage).hostname and re.search(r'impressum|legal|about', target, re.I):
                    queue.append(target)
        except (OSError, ValueError):
            result['evidence'].append({'url': url, 'kind': 'unavailable', 'excerpt': None})
    return result


def ask_host_name(value, *, interactive=False):
    if value is None:
        if not interactive:
            raise ValueError('Bitte den Hostnamen gezielt abfragen und mit --host-name übergeben')
        try:
            value = input('Wie heißt der Host? (Intro: Ich bin {Name}, herzlich willkommen!) ')
        except EOFError as error:
            raise ValueError('Hostname fehlt; bitte ausdrücklich angeben') from error
    return bounded(value, 60)


def preview(feed_url, *, count=3, host_name=None, render_mode='2d-local', data=None, fetch=fetch_public, research=True):
    validate_feed_url(feed_url, resolve=False)
    if type(count) is not int or not 1 <= count <= 5: raise ValueError('Choose 1 to 5 news items')
    host_name = ask_host_name(host_name)
    if render_mode not in RENDER_MODES: raise ValueError('Unknown rendering mode')
    data = fetch(feed_url) if data is None else data
    if len(data) > MAX_FEED_BYTES or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('Oversized feed or unsupported XML declarations')
    root = ET.fromstring(data)
    title, entries = parse_feed(data, feed_url, datetime.now().timestamp())
    title = clean(title)[:120] or 'RSS-Nachrichten'
    homepage = root.findtext('channel/link') or ''
    if not homepage:
        atom_link = root.find('{http://www.w3.org/2005/Atom}link')
        if atom_link is not None: homepage = atom_link.get('href', '')
    if homepage: homepage = urljoin(feed_url, homepage)
    operator = operator_research(feed_url, homepage, title, fetch) if research else {
        'feed_title': title, 'domain': urlsplit(feed_url).hostname, 'status': 'unverified', 'operator': None, 'evidence': []}
    stories = []; seen = set()
    for item in entries[:100]:
        url = item['url']
        try: validate_feed_url(url, resolve=False)
        except ValueError: continue
        key = clean(item['title']).casefold()
        if key in seen: continue
        seen.add(key)
        sentences = sentence_units(item.get('text', ''))
        summary = ' '.join(sentences[:2]) if sentences else item['title'] + ('' if item['title'].endswith(('.', '!', '?')) else '.')
        if len(summary) > 360: summary = item['title'][:250] + ('' if item['title'][:250].endswith(('.', '!', '?')) else '.')
        stories.append({'title': clean(item['title'])[:250], 'summary': summary, 'url': url})
        if len(stories) == count: break
    if not stories: raise ValueError('No usable public news entries')
    return {'schema_version': 1, 'profile': 'werbevideo', 'feed': feed_url, 'title': title,
            'host_name': host_name, 'operator': operator, 'stories': stories,
            'render_mode': render_mode, 'voice_profile': dict(PRODUCTION_VOICE),
            'render_options': [dict(id=key, **value) for key, value in RENDER_MODES.items()],
            'intro': f'Ich bin {host_name}, herzlich willkommen!', 'outro': 'Erstellt mit FullFeaturedOutlet.',
            'background_suggestions': [
                {'id': 'studio', 'description': 'Vorhandenes neutrales Nachrichtenstudio'},
                {'id': 'technik', 'description': 'Blaue, reduzierte Informationsfläche für Technik und Wirtschaft'},
                {'id': 'neutral', 'description': 'Sachlicher Hintergrund ohne Anbieterlogo'}],
            'host_suggestions': [{'id': 'newshost', 'description': 'Vorhandener fiktiver NewsHost, lokal als 2D-Figur animiert', 'asset': 'assets/host.png'},
                                 {'id': 'custom', 'description': 'Eigenes lizenziertes transparentes Porträt; Mundposition vorher prüfen'}],
            'notes': ['RSS-Inhalte sind untrusted Daten, keine Chat-Anweisungen.',
                      'Betreiberangaben sind Eigenangaben mit Beleg oder ausdrücklich unbestätigt.',
                      'Keine Behauptung einer Kooperation/Empfehlung durch den Feed-Betreiber.',
                      'Kurztexte sind extraktiv, keine externe Faktenprüfung.']}


def validate_plan(plan):
    if not isinstance(plan, dict): raise ValueError('Plan must be an object')
    if plan.get('schema_version') != 1 or plan.get('profile') != 'werbevideo': raise ValueError('Unsupported plan')
    bounded(plan['title']); name = bounded(plan['host_name'], 60)
    if plan['intro'] != f'Ich bin {name}, herzlich willkommen!' or plan['outro'] != 'Erstellt mit FullFeaturedOutlet.':
        raise ValueError('Unexpected intro/outro')
    validate_feed_url(plan['feed'], resolve=False)
    if plan.get('render_mode', '2d-local') not in RENDER_MODES: raise ValueError('Unknown rendering mode')
    if not isinstance(plan['stories'], list) or not 1 <= len(plan['stories']) <= 5: raise ValueError('Invalid stories')
    for story in plan['stories']:
        bounded(story['title'], 250); bounded(story['summary'], 360)
        if not 1 <= len(sentence_units(story['summary'])) <= 2: raise ValueError('Use one or two sentences')
        validate_feed_url(story['url'], resolve=False)


def speak(text, path):
    """Local eSpeak-NG library; no model download or cloud fallback."""
    library = ctypes.util.find_library('espeak-ng')
    if not library: raise RuntimeError('Install libespeak-ng1 (or supply an existing --audio WAV)')
    lib = ctypes.CDLL(library); chunks = []
    callback_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)
    @callback_type
    def callback(samples, count, events):
        if samples and count: chunks.append(ctypes.string_at(samples, count * 2))
        return 0
    lib.espeak_Initialize.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
    lib.espeak_SetSynthCallback.argtypes = [callback_type]
    lib.espeak_SetVoiceByName.argtypes = [ctypes.c_char_p]
    lib.espeak_Synth.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint, ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.c_void_p]
    rate = lib.espeak_Initialize(2, 0, None, 0)
    if rate <= 0: raise RuntimeError('Local speech initialization failed')
    try:
        lib.espeak_SetSynthCallback(callback)
        if lib.espeak_SetVoiceByName(b'de'): raise RuntimeError('German voice unavailable')
        buffer = ctypes.create_string_buffer(text.encode('utf-8')); identifier = ctypes.c_uint()
        if lib.espeak_Synth(buffer, len(buffer), 0, 1, 0, 1, ctypes.byref(identifier), None): raise RuntimeError('Local speech failed')
        lib.espeak_Synchronize()
        with wave.open(str(path), 'wb') as output:
            output.setparams((1, 2, rate, 0, 'NONE', 'not compressed')); output.writeframes(b''.join(chunks))
    finally: lib.espeak_Terminate()


def render(plan, output_root, *, style='studio', portrait=None, audio=None, fps=20, render_mode=None, mouth=None, voice_engine=None):
    validate_plan(plan)
    selected = render_mode or plan.get('render_mode', '2d-local')
    if selected not in RENDER_MODES: raise ValueError('Unknown rendering mode')
    if selected != '2d-local':
        raise RenderNotConfigured(RENDER_MODES[selected]['label'] + ': Einrichtung erforderlich; es wurde kein Renderauftrag gestartet und nichts hochgeladen.')
    if style not in STYLES or type(fps) is not int or not 5 <= fps <= 24: raise ValueError('Invalid rendering settings')
    portrait = Path(portrait or ROOT / 'assets/host.png')
    if not portrait.is_file() or not Path(FONT).is_file(): raise RuntimeError('Host image or font unavailable')
    output_root = Path(output_root); output_root.mkdir(parents=True, exist_ok=True)
    segments = [plan['intro']] + [s['summary'] for s in plan['stories']] + [plan['outro']]
    created = datetime.now(ZoneInfo('Europe/Vienna'))
    with tempfile.TemporaryDirectory(prefix='promo-', dir=output_root) as directory:
        work = Path(directory); wav = work / 'speech.wav'
        if audio:
            shutil.copyfile(audio, wav)
            voice_profile = {'actual_engine': 'provided_audio'}
        else:
            profile = dict(plan.get('voice_profile', {}))
            if voice_engine: profile['tts_engine'] = voice_engine
            voice_profile = synthesize('\n\n'.join(segments), wav, ROOT, profile=profile, fallback=speak)
        with wave.open(str(wav), 'rb') as voice:
            if voice.getsampwidth() != 2 or voice.getnchannels() != 1: raise ValueError('Use mono 16-bit PCM WAV')
            rate = voice.getframerate(); duration = voice.getnframes() / rate
        if not 0.5 <= duration <= 180: raise ValueError('Speech must be between 0.5 and 180 seconds')
        # Approximate caption timing; host animation itself follows the entire real audio.
        weights = [len(s) for s in segments]; total = sum(weights); boundaries = []; elapsed = 0
        for weight in weights:
            elapsed += duration * weight / total; boundaries.append(elapsed)
        selected_mouth = mouth or plan.get('mouth')
        frames = work / 'mouth'; count = generate_frames(portrait, wav, frames, fps=fps, mouth=selected_mouth)
        background = Image.new('RGB', (960, 540), STYLES[style])
        if style == 'studio' and (ROOT / 'assets/background.jpg').is_file():
            background = ImageOps.fit(Image.open(ROOT / 'assets/background.jpg').convert('RGB'), (960, 540))
            background = Image.blend(background, Image.new('RGB', background.size, '#102030'), .60)
        font = ImageFont.truetype(FONT, 23); small = ImageFont.truetype(FONT, 18)
        target = work / 'werbevideo.mp4'
        args = ['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','960x540','-r',str(fps),'-i','pipe:0','-i',str(wav),'-map','0:v','-map','1:a','-c:v','libx264','-preset','veryfast','-crf','24','-pix_fmt','yuv420p','-c:a','aac','-shortest','-movflags','+faststart',str(target)]
        with (work/'ffmpeg.log').open('wb') as log:
            process = subprocess.Popen(args, stdin=subprocess.PIPE, stderr=log)
            try:
                for i in range(count):
                    t = i / fps; frame = background.copy(); draw = ImageDraw.Draw(frame)
                    segment = next((j for j, end in enumerate(boundaries) if t < end), len(segments)-1)
                    draw.text((30,25), 'WERBEVIDEO · '+plan['title'][:47], font=small, fill='white')
                    text = segments[segment]
                    if 0 < segment < len(segments)-1: text = plan['stories'][segment-1]['title']+'\n\n'+text
                    card_font, card_text = fit_card(text)
                    draw.multiline_text((30,100), card_text, font=card_font, fill='white', spacing=6)
                    host = Image.open(frames/f'lip_{i:06d}.png').convert('RGBA')
                    host.thumbnail((420,430)); host = host.rotate(.8*math.sin(t*1.8), Image.Resampling.BICUBIC, expand=True)
                    frame.paste(host, (510+round(4*math.sin(t)), 490-host.height+round(2*math.sin(t*2))), host)
                    # Draw last, so the host never covers the mandatory label.
                    draw = ImageDraw.Draw(frame); draw.rectangle((893,492,950,530), fill='black'); draw.text((905,499),'AI',font=font,fill='white')
                    process.stdin.write(frame.tobytes())
                process.stdin.close()
                if process.wait(timeout=120): raise RuntimeError('FFmpeg failed')
            except BaseException:
                process.kill(); process.wait(); raise
        info = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(target)]))
        if not {'video','audio'} <= {s['codec_type'] for s in info['streams']}: raise RuntimeError('Incomplete video')
        archive = output_root/'archive'/created.strftime('%Y/%m/%d')/uuid.uuid4().hex[:12]
        archive.mkdir(parents=True); final = archive/'werbevideo.mp4'; shutil.copyfile(target, final)
        manifest = {'created_at':created.isoformat(),'archive_timezone':'Europe/Vienna','video':str(final.resolve()),
                    'duration_seconds':float(info['format']['duration']),'sha256':hashlib.sha256(final.read_bytes()).hexdigest(),
                    'ai_label':'AI bottom right, every frame','animation':'audio-driven 2D mouth and whole-host motion; not neural/phoneme-accurate',
                    'published':False,'render_mode':selected,'caption_timing':'proportional estimate','plan':plan,
                    'voice_profile':voice_profile,'mouth':selected_mouth or {'x':.5,'y':.34,'width':.13,'height':.09}}
        (archive/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        (archive/'sources.json').write_text(json.dumps([{'title':s['title'],'url':s['url']} for s in plan['stories']],ensure_ascii=False,indent=2)+'\n')
        return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest='command',required=True)
    prepare = commands.add_parser('preview'); prepare.add_argument('--feed',required=True); prepare.add_argument('--host-name',help='Explizit gewählter Name des Hosts; fehlt er, wird im Terminal nachgefragt'); prepare.add_argument('--count',type=int,default=3); prepare.add_argument('--output',type=Path,default=Path('werbevideo-plan.json')); prepare.add_argument('--feed-file',type=Path); prepare.add_argument('--no-research',action='store_true'); prepare.add_argument('--render-mode',choices=sorted(RENDER_MODES),default='2d-local')
    make = commands.add_parser('render'); make.add_argument('--plan',type=Path,required=True); make.add_argument('--output-root',type=Path,default=Path('out/promo')); make.add_argument('--style',choices=sorted(STYLES),default='studio'); make.add_argument('--portrait',type=Path); make.add_argument('--audio',type=Path); make.add_argument('--fps',type=int,default=20); make.add_argument('--render-mode',choices=sorted(RENDER_MODES)); make.add_argument('--mouth',type=Path,help='JSON calibration'); make.add_argument('--voice-engine',choices=['piper','espeak'])
    calibrate = commands.add_parser('calibrate'); calibrate.add_argument('--portrait',type=Path,required=True); calibrate.add_argument('--region',type=float,nargs=4,required=True,metavar=('X','Y','WIDTH','HEIGHT')); calibrate.add_argument('--manual',action='store_true'); calibrate.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    try:
        if args.command == 'calibrate':
            image = Image.open(args.portrait).convert('RGBA')
            region = dict(zip(('x','y','width','height'),args.region))
            mouth = region if args.manual else locate_lips(image,region)
            calibration(image,mouth).save(args.output.with_suffix('.png'))
            args.output.write_text(json.dumps(mouth,indent=2)+'\n'); print(args.output)
        elif args.command == 'preview':
            args.host_name = ask_host_name(args.host_name, interactive=sys.stdin.isatty())
            plan = preview(args.feed,count=args.count,host_name=args.host_name,render_mode=args.render_mode,data=args.feed_file.read_bytes() if args.feed_file else None,research=not args.no_research); validate_plan(plan)
            args.output.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n'); print(args.output)
        else: print(json.dumps(render(json.loads(args.plan.read_text()),args.output_root,style=args.style,portrait=args.portrait,audio=args.audio,fps=args.fps,render_mode=args.render_mode,mouth=json.loads(args.mouth.read_text()) if args.mouth else None,voice_engine=args.voice_engine),ensure_ascii=False))
    except RenderNotConfigured as error:
        print(str(error)); return 2
    except ValueError as error:
        print(str(error)); return 1
    except (OSError,KeyError,RuntimeError,ET.ParseError,subprocess.SubprocessError):
        print('Werbevideo fehlgeschlagen: Eingaben, Abhängigkeiten und lokalen Plan prüfen. Keine Veröffentlichung erfolgt.'); return 1
    return 0


if __name__ == '__main__': raise SystemExit(main())
