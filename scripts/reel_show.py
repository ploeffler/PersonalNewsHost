#!/usr/bin/env python3
"""Bounded artifact-only reel production: RSS -> local voice -> neural host -> 9:16.

No publisher, Git writes or paid service. prepare/compose can be tested offline;
model stages are explicit and fail if a real generated face/video is unavailable.
"""
import argparse
import datetime as dt
import html
import http.client
import ipaddress
import json
from pathlib import Path
import re
import shutil
import socket
import subprocess
import textwrap
import urllib.parse
import urllib.request
import wave
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
MAX_FEED_BYTES = 1_000_000
VOICE_REVISION = '5041a7a49ae5b3a0f30e6837769eb03fdbb231bd'


def clean(value):
    value = re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>', ' ', value or '', flags=re.I | re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]*>', ' ', value))).strip()


def validate_inputs(config):
    if 'test_mode' in config and type(config['test_mode']) is not bool:
        raise ValueError('test_mode must be a JSON boolean')
    for field in ['station_name', 'show_name', 'host_description', 'studio_description']:
        value = config.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > (120 if field.endswith('name') else 1000):
            raise ValueError('Missing or oversized text input: ' + field)
        if any(ord(c) < 32 for c in value):
            raise ValueError('Control characters in text input')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}(?:\.mp4)?', config.get('output_name', '')):
        raise ValueError('Output name must be a simple filename, not a path')
    count = config.get('news_count')
    if type(count) is not int or not 1 <= count <= 5:
        raise ValueError('Choose 1 to 5 news items for a reel')
    if not config.get('test_mode'):
        validate_feed_url(config.get('rss_feed', ''), resolve=False)


def validate_feed_url(url, resolve=True):
    p = urllib.parse.urlsplit(url)
    if p.scheme not in {'http', 'https'} or not p.hostname or p.username or p.password or p.port not in {None, 80, 443}:
        raise ValueError('Feed must be a public HTTP(S) URL without credentials')
    if any(k.casefold() in {'token', 'api_key', 'apikey', 'password', 'secret', 'access_token'} for k, _ in urllib.parse.parse_qsl(p.query)):
        raise ValueError('Feed URL must not include secret parameters')
    if resolve:
        addresses = socket.getaddrinfo(p.hostname, p.port or (443 if p.scheme == 'https' else 80), type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError('Private/reserved feed addresses are not allowed')
    return url


def checked_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None):
    """Connect to the checked numeric address; never re-resolve via urllib/proxy."""
    host, port = address
    records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not records or any(not ipaddress.ip_address(row[4][0]).is_global for row in records):
        raise ValueError('Feed connection resolved to a private/reserved address')
    for family, kind, protocol, _, target in records:
        connection = socket.socket(family, kind, protocol)
        try:
            if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                connection.settimeout(timeout)
            if source_address:
                connection.bind(source_address)
            connection.connect(target)
            return connection
        except OSError:
            connection.close()
    raise OSError('No public feed address could be reached')


class PublicHTTPConnection(http.client.HTTPConnection):
    def connect(self):
        self._create_connection = checked_connection
        super().connect()


class PublicHTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        self._create_connection = checked_connection
        super().connect()  # Keeps original hostname for TLS verification/SNI.


class PublicHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, request):
        return self.do_open(PublicHTTPConnection, request)


class PublicHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, request):
        return self.do_open(PublicHTTPSConnection, request, context=self._context)


class PublicRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_feed_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def read_feed(url):
    validate_feed_url(url)
    request = urllib.request.Request(url, headers={'User-Agent': 'PersonalNewsHost experimental reel'})
    with urllib.request.build_opener(urllib.request.ProxyHandler({}), PublicHTTPHandler(), PublicHTTPSHandler(), PublicRedirects()).open(request, timeout=20) as response:
        data = response.read(MAX_FEED_BYTES + 1)
    if len(data) > MAX_FEED_BYTES:
        raise ValueError('Feed exceeds 1 MB limit')
    return data


def parse_feed(data, count):
    if len(data) > MAX_FEED_BYTES or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('Oversized feed or unsupported XML declarations')
    root = ET.fromstring(data)
    atom = '{http://www.w3.org/2005/Atom}'
    nodes = root.findall('.//item') or root.findall('.//' + atom + 'entry')
    selected = []
    seen = set()
    for node in nodes[:100]:
        title = clean(node.findtext('title') or node.findtext(atom + 'title'))
        text = clean(node.findtext('description') or node.findtext(atom + 'summary') or node.findtext(atom + 'content'))
        url = clean(node.findtext('link'))
        if not url:
            link = node.find(atom + 'link')
            url = link.get('href', '') if link is not None else ''
        parsed = urllib.parse.urlsplit(url)
        if not title or title.casefold() in seen or parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username or parsed.password:
            continue
        seen.add(title.casefold())
        selected.append({'title': title[:250], 'text': ' '.join(text.split()[:14]),
                         'url': urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))})
        if len(selected) == count:
            break
    if len(selected) < count:
        raise ValueError('Feed has fewer usable distinct items than requested')
    return selected


def prepare(config, work, data=None):
    validate_inputs(config)
    work.mkdir(parents=True, exist_ok=True)
    if config.get('test_mode'):
        entries = [{'title': 'Dies ist eine technische Testsendung.', 'text': '', 'url': 'https://example.org/fixture'}]
        if config['news_count'] != 1:
            raise ValueError('Smoke test uses exactly one fixture item')
    else:
        entries = parse_feed(data if data is not None else read_feed(config['rss_feed']), config['news_count'])
    parts = [{'text': config['station_name'] + '. ' + config['show_name'] + '.', 'title': config['show_name']}]
    for entry in entries:
        headline = ' '.join(entry['title'].split()[:22])
        parts.append({'text': headline.rstrip('.!?') + '. ' + entry['text'], 'title': entry['title']})
    (work / 'plan.json').write_text(json.dumps({'config': config, 'entries': entries, 'parts': parts}, ensure_ascii=False, indent=2))
    return entries


def speak(work, piper):
    try:
        from .reel_models import download
    except ImportError:
        from reel_models import download
    voice = ROOT / '.reel-models/de_DE-thorsten-medium.onnx'
    base = 'https://huggingface.co/rhasspy/piper-voices/resolve/' + VOICE_REVISION + '/de/de_DE/thorsten/medium/'
    for suffix in ['', '.json']:
        download(base + voice.name + suffix, Path(str(voice) + suffix))
    plan = json.loads((work / 'plan.json').read_text())
    segments, cursor = [], 0.0
    params = None
    samples = []
    for index, part in enumerate(plan['parts']):
        path = work / ('speech-' + str(index) + '.wav')
        subprocess.run([str(piper), '--model', str(voice), '--output_file', str(path)], input=part['text'], text=True, check=True, timeout=120)
        with wave.open(str(path)) as source:
            current = source.getparams()[:3]
            if params is not None and params != current:
                raise RuntimeError('Voice output format changed')
            params = current
            frames = source.readframes(source.getnframes())
            duration = source.getnframes() / source.getframerate()
            samples.append(frames)
        segments.append({**part, 'start': cursor, 'end': cursor + duration})
        cursor += duration
    if not 0 < cursor <= 90:
        raise ValueError('Speech exceeds 90 seconds; request fewer/shorter news items')
    with wave.open(str(work / 'speech.wav'), 'wb') as target:
        target.setparams((*params, 0, 'NONE', 'not compressed'))
        for frames in samples:
            target.writeframes(frames)
    plan.update(segments=segments, duration=cursor)
    (work / 'plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2))


def caption_card(config, title, path):
    from PIL import Image, ImageDraw, ImageFont
    card = Image.new('RGBA', (720, 1280), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    def font(size):
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)
    draw.rectangle((0, 0, 720, 175), fill=(10, 20, 40, 235))
    draw.text((28, 24), clean(config['station_name'])[:32], font=font(28), fill='white')
    for index, line in enumerate(textwrap.wrap(clean(config['show_name']), 30)[:2]):
        draw.text((28, 72 + index * 40), line, font=font(34), fill='white')
    draw.rectangle((18, 830, 702, 1160), fill=(10, 20, 40, 235))
    for index, line in enumerate(textwrap.wrap(clean(title), 30)[:7]):
        draw.text((38, 850 + index * 40), line, font=font(30), fill='white')
    draw.text((28, 1180), 'Quellen im Begleitartefakt', font=font(20), fill='white')
    draw.rectangle((540, 1220, 714, 1274), fill=(180, 0, 0, 255))
    draw.text((551, 1233), 'AI-GENERIERT', font=font(19), fill='white')
    card.save(path)


def compose(work, destination):
    plan = json.loads((work / 'plan.json').read_text())
    config = plan['config']
    validate_inputs(config)
    day = dt.datetime.now(ZoneInfo('Europe/Vienna')).strftime('%Y/%m/%d')
    folder = destination / day
    folder.mkdir(parents=True, exist_ok=True)
    name = config['output_name'].removesuffix('.mp4')
    video = folder / (name + '.mp4')
    args = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-filter_complex_threads', '1',
            '-loop', '1', '-i', str(work / 'studio.png'), '-i', str(work / 'talking-host.mp4')]
    filters = ['[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1[bg]',
               '[1:v]scale=576:576,setsar=1[host]', '[bg][host]overlay=72:190[scene]']
    previous = 'scene'
    for index, part in enumerate(plan['segments']):
        path = work / ('card-' + str(index) + '.png')
        caption_card(config, part['title'], path)
        args += ['-loop', '1', '-i', str(path)]
        output = 'card' + str(index)
        filters.append(f'[{previous}][{index+2}:v]overlay=0:0:enable=\'between(t,{part["start"]:.6f},{part["end"]:.6f})\'[{output}]')
        previous = output
    args += ['-i', str(work / 'speech.wav'), '-filter_complex', ';'.join(filters), '-map', '[' + previous + ']',
             '-map', str(len(plan['segments']) + 2) + ':a', '-t', str(plan['duration']), '-r', '25', '-c:v', 'libx264',
             '-preset', 'veryfast', '-crf', '24', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-movflags', '+faststart', str(video)]
    subprocess.run(args, check=True, timeout=300)
    if video.stat().st_size > 90_000_000:
        video.unlink()
        raise RuntimeError('Reel exceeds artifact size limit')
    (folder / (name + '-sources.json')).write_text(json.dumps(plan['entries'], ensure_ascii=False, indent=2))
    (folder / (name + '-transcript.txt')).write_text('\n\n'.join(p['text'] for p in plan['parts']))
    manifest = {'video': str(video.relative_to(destination)), 'station': config['station_name'], 'show': config['show_name'],
                'format': '720x1280 / 9:16', 'animation': 'SadTalker CPU, neural talking head', 'language': 'de',
                'ai_label': 'bottom-right', 'paid_api_calls': 0, 'repository_commit': False,
                'duration_seconds': plan['duration'], 'fictional_presenter': True,
                'models': {'images': 'stabilityai/sd-turbo', 'avatar': 'OpenTalker/SadTalker', 'voice': 'de_DE-thorsten-medium'},
                'retention_days': 1, 'source_verification': 'extractive RSS text; not independent fact verification'}
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    (destination / 'MODEL-NOTICES.txt').write_text('Images: https://huggingface.co/stabilityai/sd-turbo (see model license, commercial terms may vary).\nAvatar: https://github.com/OpenTalker/SadTalker (Apache-2.0).\nVoice: https://huggingface.co/rhasspy/piper-voices/blob/main/de/de_DE/thorsten/medium/MODEL_CARD\nGenerated presenter/studio are fictional. No source images depicting real news events are fabricated.\n')
    print(video.resolve())
    return video


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'speak', 'compose'])
    parser.add_argument('--config', type=Path, default=Path('.reel-work/request.json'))
    parser.add_argument('--work', type=Path, default=Path('.reel-work'))
    parser.add_argument('--output', type=Path, default=Path('out/chat-reel'))
    parser.add_argument('--piper', type=Path, default=Path('.reel-image/bin/piper'))
    args = parser.parse_args()
    if args.stage == 'prepare':prepare(json.loads(args.config.read_text()), args.work)
    elif args.stage == 'speak':speak(args.work, args.piper.resolve())
    else:compose(args.work, args.output)


if __name__ == '__main__':main()
