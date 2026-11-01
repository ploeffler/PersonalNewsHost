#!/usr/bin/env python3
"""Local authenticated sender page. Run: python3 scripts/sender_style_server.py."""
import argparse
import fcntl
import hmac
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import threading
import time
from urllib.parse import urlsplit
try:
    from .sender_style import ROOT, Store, Conflict, seed
    from .style_research import analyze
    from .style_preview import Worker, policy, public_policy
except ImportError:
    from sender_style import ROOT, Store, Conflict, seed
    from style_research import analyze
    from style_preview import Worker, policy, public_policy

ASSETS=ROOT/'assets/sender-style'


class App:
    def __init__(self,store,password,config=None):
        if len(password)<16:raise ValueError('Senderstil-Passwort muss mindestens 16 Zeichen haben')
        self.store=store;self.password=password;self.config=config or ROOT/'config.json'
        if store.state()['revision']==0 and Path(self.config).is_file():
            store.save_draft(seed(json.loads(Path(self.config).read_text())),0)
        self.sessions={};self.failures=[];self.auth_lock=threading.Lock()

    def login(self,password):
        now=time.monotonic()
        with self.auth_lock:
            self.failures=[t for t in self.failures if t>now-60]
            if len(self.failures)>=8:raise ValueError('Zu viele Anmeldeversuche; eine Minute warten')
            if not isinstance(password,str) or not hmac.compare_digest(password.encode(),self.password.encode()):
                self.failures.append(now);raise ValueError('Anmeldung fehlgeschlagen')
            self.sessions={k:v for k,v in self.sessions.items() if v['until']>now}
            token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(32)
            self.sessions[token]={'csrf':csrf,'until':now+8*3600}
            return token,csrf

    def session(self,cookie):
        try:
            parsed=SimpleCookie();parsed.load(cookie or '')
            token=parsed['pnh_style'].value
        except (KeyError,ValueError):return None
        with self.auth_lock:
            session=self.sessions.get(token)
            return session if session and session['until']>time.monotonic() else None


class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,app):
        if address[0]!='127.0.0.1':raise ValueError('Senderstil-Editor nur an Loopback binden')
        self.app=app
        super().__init__(address,Handler)


class Handler(BaseHTTPRequestHandler):
    server_version='PNHSenderStyle'
    def setup(self):
        super().setup();self.connection.settimeout(10)
    def log_message(self,*args):pass
    def valid_host(self):return self.headers.get('Host')=='127.0.0.1:'+str(self.server.server_port)
    def reply(self,status,data,kind='application/json; charset=utf-8',cookie=None):
        raw=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers();self.wfile.write(raw)
    def authenticated(self,mutate=False):
        session=self.server.app.session(self.headers.get('Cookie'))
        if not session:
            self.reply(401,{'error':'Bitte anmelden'});return None
        if mutate and not hmac.compare_digest(self.headers.get('X-CSRF-Token',''),session['csrf']):
            self.reply(403,{'error':'CSRF-Prüfung fehlgeschlagen'});return None
        return session
    def do_GET(self):
        if not self.valid_host():self.reply(403,{'error':'Ungültiger Host'});return
        path=urlsplit(self.path).path
        static={'/':('index.html','text/html; charset=utf-8'),'/app.js':('app.js','text/javascript; charset=utf-8'),'/style.css':('style.css','text/css; charset=utf-8')}
        if path in static:
            name,kind=static[path];self.reply(200,(ASSETS/name).read_bytes(),kind);return
        session=self.authenticated()
        if not session:return
        app=self.server.app
        if path=='/api/state':
            data=app.store.state();data['csrf']=session['csrf'];data['provider']=public_policy(len(app.store.styles));self.reply(200,data)
        elif path=='/api/export':
            data=app.store.state();self.reply(200,{'sender_style':{'version':data['active_version'],'style':data['active']}})
        elif re.fullmatch(r'/api/jobs/[a-f0-9]{64}',path):
            try:
                job=app.store.job_context(path.rsplit('/',1)[1]);job['snapshot']=json.loads(job['snapshot']);self.reply(200,job)
            except ValueError:self.reply(404,{'error':'Auftrag nicht gefunden'})
        elif re.fullmatch(r'/images/[a-f0-9]{64}\.png',path):
            name=path.rsplit('/',1)[1];target=app.store.root/'images'/name
            try:job=app.store.job_context(name[:-4])
            except ValueError:job={}
            if job.get('status')!='complete' or not target.is_file() or target.is_symlink():self.reply(404,{'error':'Vorschau nicht verfügbar'})
            else:self.reply(200,target.read_bytes(),'image/png')
        elif re.fullmatch(r'/examples/[a-z0-9_]+\.png',path):
            name=path.rsplit('/',1)[1]
            allowed={s['style_id']+'.png' for s in app.store.styles}
            if name not in allowed:self.reply(404,{'error':'Beispiel fehlt'})
            else:self.reply(200,(ROOT/'assets/style-examples'/name).read_bytes(),'image/png')
        else:self.reply(404,{'error':'Nicht gefunden'})
    def do_POST(self):
        origin='http://127.0.0.1:'+str(self.server.server_port)
        if not self.valid_host() or self.headers.get('Origin')!=origin:
            self.reply(403,{'error':'Ungültiger Ursprung'});return
        if self.headers.get('Content-Type')!='application/json':
            self.reply(415,{'error':'JSON erforderlich'});return
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=20000:raise ValueError('Ungültige Anfragegröße')
            body=json.loads(self.rfile.read(size))
            if not isinstance(body,dict):raise ValueError('JSON-Objekt erforderlich')
            path=urlsplit(self.path).path;app=self.server.app
            if path=='/api/login':
                token,csrf=app.login(body.get('password'))
                self.reply(200,{'csrf':csrf},cookie='pnh_style='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800');return
            if not self.authenticated(mutate=True):return
            if path=='/api/logout':
                cookie=SimpleCookie();cookie.load(self.headers.get('Cookie',''))
                with app.auth_lock:app.sessions.pop(cookie['pnh_style'].value,None)
                self.reply(200,{},cookie='pnh_style=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0');return
            if path=='/api/research':self.reply(200,analyze(body.get('url')));return
            if path in ('/api/draft','/api/seed','/api/adopt','/api/restore'):
                revision=body.get('revision')
                if type(revision) is not int:raise ValueError('Entwurfsrevision fehlt')
            if path=='/api/draft':data=app.store.save_draft(body.get('draft'),revision)
            elif path=='/api/seed':
                config=json.loads(Path(app.config).read_text());data=app.store.save_draft(seed(config),revision)
            elif path=='/api/restore':data=app.store.restore(body.get('version'),revision)
            elif path=='/api/adopt':
                if type(body.get('allow_paid',False)) is not bool:raise ValueError('Ungültige Kostenfreigabe')
                provider=policy();provider['allow_paid']=provider['allow_paid'] and body.get('allow_paid',False)
                data=app.store.adopt(revision,provider)
            elif path=='/api/retry':
                if type(body.get('allow_uncertain',False)) is not bool:raise ValueError('Ungültige Kostenbestätigung')
                data=app.store.retry(body.get('job'),body.get('allow_uncertain',False))
            elif path=='/api/reissue':
                if body.get('allow_paid') is not True or type(body.get('allow_uncertain',False)) is not bool:
                    raise ValueError('Neue Kostenfreigabe erforderlich')
                provider=policy()
                if not os.environ.get('PNH_STYLE_IMAGE_API_KEY'):
                    raise ValueError('Bildprovider-Zugang fehlt')
                data=app.store.reissue(body.get('batch'),provider,body.get('allow_uncertain',False))
            else:self.reply(404,{'error':'Nicht gefunden'});return
            self.reply(200,data)
        except Conflict as error:self.reply(409,{'error':str(error)})
        except (ValueError,KeyError,TypeError):self.reply(400,{'error':'Eingaben, Entwurf oder Recherche prüfen; aktive CI bleibt bei Validierungsfehlern unverändert.'})
        except Exception:self.reply(503,{'error':'Lokaler Dienst oder URL-Recherche vorübergehend nicht verfügbar'})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8766)
    parser.add_argument('--state',type=Path,default=ROOT/'state/sender-style')
    args=parser.parse_args()
    if not 1024<=args.port<=65535:parser.error('Port muss 1024..65535 sein')
    store=Store(args.state)
    with (store.root/'server.lock').open('w') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise SystemExit('Für dieses Datenverzeichnis läuft bereits ein Senderstil-Editor') from None
        password=os.environ.get('PNH_STYLE_ADMIN_PASSWORD') or secrets.token_urlsafe(24)
        app=App(store,password);store.recover();stop=threading.Event()
        server=Server(('127.0.0.1',args.port),app)
        worker=threading.Thread(target=Worker(store).run,args=(stop,),daemon=True);worker.start()
        print('Senderseite: http://127.0.0.1:'+str(args.port),flush=True)
        if not os.environ.get('PNH_STYLE_ADMIN_PASSWORD'):print('Temporäres lokales Passwort: '+password,flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:stop.set();server.server_close();worker.join(timeout=5)


if __name__=='__main__':main()

