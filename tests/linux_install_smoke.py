#!/usr/bin/env python3
"""Fresh-install CI proof: repeat setup, preserve data, render real local speech, serve preview."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from unittest.mock import patch
from urllib.request import urlopen
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from scripts import generate, local_runtime
    before = (ROOT/'config.json').read_bytes()
    marker = '.t181-' + uuid.uuid4().hex
    sentinels = [ROOT/'state'/marker, ROOT/'models'/marker, ROOT/'archive'/marker]
    try:
        for path in sentinels:
            with path.open('xb') as stream:stream.write(b'preserve-existing-user-data')
        result = subprocess.run([sys.executable, str(ROOT/'scripts/install_linux.py'), '--install'],
                                check=True, capture_output=True, text=True, timeout=180)
        if not json.loads(result.stdout)['reused_dependencies']:
            raise RuntimeError('Repeated setup unexpectedly reinstalled dependencies')
        if (ROOT/'config.json').read_bytes() != before or any(p.read_bytes() != b'preserve-existing-user-data' for p in sentinels):
            raise RuntimeError('Repeat setup changed protected data')
        config = json.loads((ROOT/'config.example.json').read_text())
        config.pop('shows', None)
        config.update(title='Linux installation smoke', feeds=['https://fixture.example/rss'],
                      max_items=1, station_logo='', tts_engine='espeak', target_duration_seconds=120,
                      providers=[], provider_tasks={}, media={'mode':'off'}, production={'parallel_workers':1})
        config['editorial']={'pipeline':{'enabled':False},'crosscheck':{'enabled':False}}
        config['presenter_settings']={'background':'assets/missing.jpg', 'portrait':'assets/missing.png',
            'scenes':{'intro_mode':'static','intro_static_type':'color','show_headlines':False}}
        fixture = (ROOT/'tests/fixtures/offline-feeds/news.xml').read_bytes()
        def feed(url):
            if url != 'https://fixture.example/rss':raise RuntimeError('Unexpected external fetch')
            return fixture
        with tempfile.TemporaryDirectory(prefix='install-smoke-',dir=ROOT/'out') as directory:
            root=Path(directory);path=root/'config.json';path.write_text(json.dumps(config))
            paths=local_runtime.layout(ROOT);paths['productions']=root/'productions'
            with patch.object(generate,'fetch',side_effect=feed),patch.object(generate,'extract_article_text',return_value=''):
                produced=local_runtime.produce(path,'main',paths)
            quality=json.loads((produced/'production-quality.json').read_text())
            if quality['status']!='passed':raise RuntimeError('Production quality gate failed')
            public=root/'public';shutil.copytree(produced,public)
            handler=partial(SimpleHTTPRequestHandler,directory=str(public))
            with ThreadingHTTPServer(('127.0.0.1',0),handler) as server:
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                try:
                    base='http://127.0.0.1:'+str(server.server_port)
                    with urlopen(base+'/index.html',timeout=10) as response:
                        if response.status!=200:raise RuntimeError('Local page unavailable')
                    with urlopen(base+'/latest.mp4',timeout=10) as response:
                        if len(response.read(2048))<1000:raise RuntimeError('Local video unavailable')
                finally:
                    server.shutdown();thread.join(timeout=5)
            print(json.dumps({'repeat_install':'passed','user_data_preserved':True,
                              'local_http_video':'passed','real_voice':'espeak-ng', 'quality':quality}))
    finally:
        for path in sentinels:path.unlink(missing_ok=True)


if __name__=='__main__':main()
