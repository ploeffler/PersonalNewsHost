#!/usr/bin/env python3
"""Build a labelled offline example of the initial Allgemein newsroom's Newsshow."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
import uuid
from zoneinfo import ZoneInfo

try:
    from . import generate
    from .produce_show import produce
except ImportError:
    import generate
    from produce_show import produce

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/example-show.json'
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def configuration(fixture):
    return {
        'title':'Newsshow – Beispiel', 'language':'de', 'voice':'de',
        'feeds':['https://example.invalid/beispiel/rss'], 'max_items':3,
        'max_description_chars':300, 'tts_engine':'espeak', 'voice_pitch_semitones':0,
        'editorial':{'pipeline':{'enabled':False},'crosscheck':{'enabled':False},'topic_clustering':{'enabled':False}},
        'media':{'mode':'off','web_image_fallback':False,'enhancement':'off'},
        'article_enrichment':{'enabled':False},
        'automation':{'enabled':False,'timezone':'Europe/Vienna'},
        'presenter_settings':{'name':'NewsHost','portrait':'assets/presenter.png',
            'background':'assets/background.jpg','desk_foreground':'assets/desk_foreground.png',
            'lip_sync':{'enabled':False},
            'scenes':{'intro_mode':'avatar','show_headlines':True,
                'intro_text':'Willkommen zur Newsshow der Redaktion Allgemein. Sie sehen eine vorbereitete Beispielsendung mit festen Testbeiträgen.',
                'outro_text':'Das war unsere Beispielsendung. Alle Beiträge dienen der Vorschau. Es wurde keine aktuelle Nachrichtenquelle abgerufen.'}},
        'shows':[{'id':'main'}],
    }


@contextmanager
def fixture_inputs(fixture):
    """Only this explicit fixture build substitutes input; restore all state afterwards."""
    stories=fixture['stories']
    original_feed,original_article=generate.items_from_feed,generate.extract_article_text
    original_run=generate.run
    original_connect,original_connect_ex,original_dns=socket.socket.connect,socket.socket.connect_ex,socket.getaddrinfo
    def deny(*args,**kwargs):raise OSError('Example show has no network access')
    def demo_run(args):
        # The legacy renderer has a hardcoded LIVE strapline; this fixture is not live.
        return original_run([part.replace("text='KI  /  NEWS  /  LIVE'", "text='KI  /  NEWS  /  BEISPIEL'") if isinstance(part,str) else part for part in args])
    generate.run=demo_run
    generate.items_from_feed=lambda url:[(s['title'],s['text'],s['url'],[]) for s in stories]
    generate.extract_article_text=lambda url:next((s['text'] for s in stories if s['url']==url),'')
    socket.socket.connect=deny;socket.socket.connect_ex=deny;socket.getaddrinfo=deny
    try:yield
    finally:
        generate.items_from_feed,generate.extract_article_text=original_feed,original_article
        generate.run=original_run
        socket.socket.connect,socket.socket.connect_ex,socket.getaddrinfo=original_connect,original_connect_ex,original_dns


def inspect_video(path):
    result=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],check=True,capture_output=True,text=True)
    info=json.loads(result.stdout)
    if not any(s['codec_type']=='video' for s in info['streams']) or not any(s['codec_type']=='audio' for s in info['streams']):
        raise RuntimeError('Example requires video and audio')
    if float(info['format']['duration'])<=0:raise RuntimeError('Invalid video duration')
    return info


def finalize(video):
    target=video.with_name('labelled.tmp.mp4')
    try:
        subprocess.run(['ffmpeg','-y','-v','error','-i',str(video),'-vf',
            f'drawtext=fontfile={FONT}:text=AI:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.8:boxborderw=8:x=w-tw-24:y=h-th-24',
            '-c:v','libx264','-preset','veryfast','-crf','23','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(target)],check=True,timeout=480)
        inspect_video(target)
        target.replace(video)
    finally:target.unlink(missing_ok=True)


def build(output_root,fixture_path=FIXTURE):
    fixture=json.loads(Path(fixture_path).read_text(encoding='utf-8'))
    if fixture.get('fixture_id')!='newsshow-allgemein-de-v1' or len(fixture.get('stories',[]))!=3:
        raise ValueError('Unsupported example fixture')
    output_root=Path(output_root)
    with fixture_inputs(fixture):destination=produce(configuration(fixture),'main',output_root)
    video=destination/'latest.mp4'
    finalize(video)
    # Legacy producer may have created another final copy before the demo overlay.
    for copy in destination.rglob('*.mp4'):
        if copy!=video:shutil.copyfile(video,copy)
    info=inspect_video(video)
    created=datetime.now(timezone.utc)
    production=created.strftime('%H%M%S')+'-'+uuid.uuid4().hex[:8]
    archive=output_root/'archive'/created.astimezone(ZoneInfo('Europe/Vienna')).strftime('%Y/%m/%d')/'main'/production
    archive.mkdir(parents=True)
    shutil.copyfile(video,archive/'example-de.mp4')
    manifest={'fixture_id':fixture['fixture_id'],'newsroom':fixture['newsroom'],'show_id':'main',
        'language':'de','is_example':True,'live_sources':False,'published':False,'ai_label':'AI, bottom right, all frames',
        'created_at':created.isoformat(),'archive_timezone':'Europe/Vienna','archive':str(archive.relative_to(output_root)/'example-de.mp4'),
        'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'duration_seconds':float(info['format']['duration'])}
    for path in [output_root/'example-manifest.json',archive/'manifest.json']:
        path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    subprocess.run(['ffmpeg','-y','-v','error','-ss','1','-i',str(video),'-frames:v','1',str(destination/'preview.png')],check=True,timeout=60)
    (destination/'index.html').write_text('<!doctype html><html lang="de"><meta charset="utf-8"><title>Newsshow – Beispiel</title><h1>Redaktion Allgemein – Beispielsendung</h1><p>Feste Testbeiträge, keine aktuellen Nachrichten.</p><video controls width="960" poster="preview.png"><source src="latest.mp4" type="video/mp4"><track kind="subtitles" src="subtitles.de.vtt" srclang="de" label="Deutsch"></video><p><a href="transcript.txt">Sprechertext</a></p></html>',encoding='utf-8')
    (output_root/'README.txt').write_text('Vorbereitete Newsshow der Redaktion Allgemein.\nmain/latest.mp4 abspielen oder main/index.html lokal öffnen.\nFeste Testbeiträge, keine aktuellen Nachrichten. Keine Veröffentlichung.\nDas Datumsarchiv und example-manifest.json liegen ebenfalls in diesem Paket.\n',encoding='utf-8')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root',type=Path,default=ROOT/'out/example-show')
    args=parser.parse_args()
    print(json.dumps(build(args.output_root),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
